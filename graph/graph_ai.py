# graph/graph_ai.py

from typing import Dict, Any
from langgraph.graph import StateGraph

from schemas.planner import TaskType  
# ---------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------

def _to_dict(obj):
    """Safely convert Pydantic models or enums to plain dicts/values."""
    if hasattr(obj, "model_dump"):  # pydantic v2
        return obj.model_dump()
    if hasattr(obj, "dict"):        # pydantic v1
        return obj.dict()
    return obj


# ---------------------------------------------------------------------
# Planner node
# ---------------------------------------------------------------------

def planner_node(state: Dict[str, Any], planner) -> Dict[str, Any]:
    """
    First node: calls PlannerAgent to produce a plan of subtasks.
    """
    print("\n" + "=" * 80)
    print("[planner_node] LLM-first planning for:", state.get("student_input"))

    q = (state.get("user_query") or state.get("student_input") or "").strip()
    state["student_input"] = q

    # Ensure outputs list exists
    if "outputs" not in state or state["outputs"] is None:
        state["outputs"] = []

    try:
        plan_obj = planner.plan(q)
        plan = _to_dict(plan_obj)

        routes = []
        for s in plan.get("subtasks", []):
            if isinstance(s, dict):
                routes.append(s.get("task"))
            else:
                s_dict = _to_dict(s)
                routes.append(s_dict.get("task"))

        routing_info = {
            "routes": routes,
            "llm_used": bool(plan.get("llm_used", False)),
            "router_confidence": float(plan.get("router_confidence", 0.0)),
            "reasoning": plan.get("reasoning", ""),
        }

        print("\n[planner_node] Routing info:", routing_info)

        state["plan"] = plan
        state["routing_info"] = routing_info
        return state

    except Exception as e:
        # If PlannerAgent ever blows up, we hard-fall back to a reject plan
        print("[planner_node] ERROR in planner:", e)

        fallback_plan = {
            "subtasks": [
                {
                    "task": "chat",
                    "payload": {"message": "off_topic"},
                }
            ],
            "router_confidence": 0.0,
            "reasoning": f"Planner failed: {e}",
            "rules_triggered": ["planner_error"],
            "llm_used": False,
        }
        state["plan"] = fallback_plan
        state["routing_info"] = {
            "routes": ["chat"],
            "llm_used": False,
            "router_confidence": 0.0,
            "reasoning": f"Planner failed: {e}",
        }
        return state


# ---------------------------------------------------------------------
# Router node + conditional routing
# ---------------------------------------------------------------------

def router_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Router node: picks the next subtask from the plan and writes it into
    state['current_subtask'], along with tracking _subtask_index.
    """
    print("\n" + "=" * 80)
    print("[router_node] Starting router_node")
    print(f"[router_node] State keys: {list(state.keys())}")

    plan = state.get("plan")
    if plan is None:
        print("[router_node] No plan found, marking end of execution")
        state["current_subtask"] = None
        state["_routing_decision"] = "__end__"
        return state

    plan_dict = _to_dict(plan)
    subtasks = plan_dict.get("subtasks", [])
    print(f"[router_node] Subtasks: {subtasks}")

    idx = state.get("_subtask_index", 0)
    print(f"[router_node] Current subtask index: {idx}")

    if idx >= len(subtasks):
        print("[router_node] No more subtasks, marking end of execution")
        state["current_subtask"] = None
        state["_routing_decision"] = "__end__"
        return state

    current = _to_dict(subtasks[idx])
    state["_subtask_index"] = idx + 1
    state["current_subtask"] = current

    if "routing_info" not in state and "routing_info" in plan_dict:
        state["routing_info"] = plan_dict["routing_info"]

    print(f"[router_node] Selected subtask: {current}")
    return state


def route_from_current_subtask(state: Dict[str, Any]) -> str:
    """
    Conditional routing function for LangGraph.
    """
    print("\n" + "=" * 80)
    print("[route_from_current_subtask] Deciding next node")
    print(f"[route_from_current_subtask] State keys: {list(state.keys())}")

    if state.get("_routing_decision") == "__end__":
        print("[route_from_current_subtask] _routing_decision is __end__")
        return "__end__"

    current = state.get("current_subtask")
    if not current:
        print("[route_from_current_subtask] No current_subtask, ending execution")
        return "__end__"

    task = (current.get("task") or "").lower()
    payload = current.get("payload") or {}
    payload_msg = (payload.get("message") or "").lower()

    print(f"[route_from_current_subtask] current task={task}, payload={payload}")

    if task == "solve":
        print("[route_from_current_subtask] → math")
        return "math"

    if task == "explain":
        print("[route_from_current_subtask] → tutor")
        return "tutor"

    if task == "reject" or (task == "chat" and payload_msg == "off_topic"):
        print("[route_from_current_subtask] → reject")
        return "reject"

    print(f"[route_from_current_subtask] Unknown task '{task}', routing to reject")
    return "reject"


# ---------------------------------------------------------------------
# Tutor node
# ---------------------------------------------------------------------

def tutor_node(state: Dict[str, Any], tutor_mod) -> Dict[str, Any]:
    """
    Wraps the module-level tutor_agent.tutor_node(state).
    """
    print("\n" + "=" * 80)
    print("[tutor_node] Starting tutor_node")
    print(f"[tutor_node] State keys: {list(state.keys())}")

    if "outputs" not in state or state["outputs"] is None:
        state["outputs"] = []

    current = state.get("current_subtask")
    print("[tutor_node] Current subtask:", current if current else "N/A")

    # We optionally drop the topic into state['plan']['topic'] to help TutorAgent.
    if current and (current.get("task") or "").lower() == "explain":
        topic = current.get("payload", {}).get("topic") or state.get("student_input", "")
        # Inject a simple topic into a lightweight plan for TutorAgent, without
        # touching the full Planner plan structure.
        state["plan_for_tutor"] = {"topic": topic}
    else:
        topic = state.get("student_input", "")
        state["plan_for_tutor"] = {"topic": topic}

    print("[tutor_node] Using topic for tutor:", topic)

    # Build a clean sub-state TutorAgent expects:
    tutor_state = {
        "student_input": state.get("student_input"),
        "conversation_id": state.get("conversation_id"),
        "turn_index": state.get("turn_index"),
        "plan": state.get("plan_for_tutor"),
    }

    # Call into the actual TutorAgent implementation
    result = tutor_mod.tutor_node(tutor_state)

    # Extract fields from tutor result
    response = result.get("tutor_response") or result.get("output") or ""
    rag_metadata = result.get("rag_metadata", {})
    is_fallback = bool(result.get("is_fallback_response", False))

    state["output"] = response
    state["rag_metadata"] = rag_metadata
    state["is_fallback_response"] = is_fallback

    state["outputs"].append(
        {
            "response": response,
            "error": result.get("error", ""),
        }
    )

    state["node_processing"] = {
        "node_type": "tutor",
        "task": (current or {}).get("task", "explain"),
        "topic": topic,
    }

    print("[tutor_node] Response (first 120 chars):", repr(response[:120]))
    return state


# ---------------------------------------------------------------------
# Math node
# ---------------------------------------------------------------------

def math_node(state: Dict[str, Any], math_agent) -> Dict[str, Any]:
    """
    Wraps MathAgent.math_node(plan_dict).
    """
    print("\n" + "=" * 80)
    print("[math_node] Starting math_node")
    print(f"[math_node] State keys: {list(state.keys())}")

    if "outputs" not in state or state["outputs"] is None:
        state["outputs"] = []

    current = state.get("current_subtask")
    print("[math_node] Current subtask:", current if current else "N/A")

    if current and (current.get("task") or "").lower() == "solve":
        problem = current.get("payload", {}).get("problem") or state.get("student_input", "")
    else:
        problem = state.get("student_input", "")

    print("[math_node] Using problem:", problem)

    # Build the minimal MathTask-compatible dict:
    math_plan = {
        "agent": "MathAgent",
        "task": "solve",
        "problem": problem,
        # Optional: later you can add "topic" or "constraints" here if you want
        # "topic": ...,
        # "constraints": {"level": "student", "precision": 4, "max_words": 700},
    }

    # Call MathAgent.math_node
    result_obj = math_agent.math_node(math_plan)

    # MathAgent.math_node returns a MathAgentOutput (Pydantic), so convert to dict:
    result = _to_dict(result_obj)

    final_answer = result.get("final_answer", "")
    steps = result.get("steps", [])
    confidence = result.get("confidence", None)

    # Format a human-facing string for this math turn
    lines = []
    if final_answer:
        lines.append(f"**Final Answer:** {final_answer}")
    if steps:
        lines.append("\n**Explanation:**")
        for i, s in enumerate(steps, start=1):
            # Each s is a Step model: {title, text}
            text = getattr(s, "text", None) or (s.get("text") if isinstance(s, dict) else str(s))
            lines.append(f"{i}. {text}")
    if confidence is not None:
        lines.append(f"\n(Confidence: {confidence:.2f})")

    response = "\n".join(lines) if lines else final_answer

    state["output"] = response
    state["math_result"] = result
    state["outputs"].append(
        {
            "response": response,
            "error": result.get("notes", ""),
        }
    )

    state["node_processing"] = {
        "node_type": "math",
        "task": (current or {}).get("task", "solve"),
        "problem": problem,
    }

    print("[math_node] Response (first 120 chars):", repr(response[:120]))
    return state


# ---------------------------------------------------------------------
# Reject & feedback nodes
# ---------------------------------------------------------------------

def reject_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Handles off-topic or invalid queries.
    """
    print("\n" + "=" * 80)
    print("[reject_node] Starting reject_node")

    if "outputs" not in state or state["outputs"] is None:
        state["outputs"] = []

    msg = "This question is outside the course scope. Please ask me a COMP-related question."
    state["output"] = msg
    state["outputs"].append({"response": msg, "error": ""})
    state["node_processing"] = {
        "node_type": "reject",
        "task": "reject",
    }
    state["is_fallback_response"] = True

    print("[reject_node] Response:", msg)
    return state


def feedback_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Final node: currently just marks completion.
    """
    print("\n" + "=" * 80)
    print("[feedback_node] Starting feedback_node")
    print(f"[feedback_node] Final state keys: {list(state.keys())}")

    # You can add FeedbackAgent calls here later if you want.
    state.setdefault("final_response", "OK")
    return state


# ---------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------

def build_ai_tutor_graph(planner, tutor_mod, math_agent):
    """
    Build and compile the LangGraph StateGraph for the tutor.

    - planner: PlannerAgent instance
    - tutor_mod: agents.tutor_agent module (exposes tutor_node(state))
    - math_agent: MathAgent instance (exposes math_node(plan_dict))
    """
    g = StateGraph(dict)

    # Nodes
    g.add_node("planner", lambda s: planner_node(s, planner))
    g.add_node("router", router_node)
    g.add_node("tutor", lambda s: tutor_node(s, tutor_mod))
    g.add_node("math", lambda s: math_node(s, math_agent))
    g.add_node("reject", reject_node)
    g.add_node("feedback", feedback_node)

    # Entry point
    g.set_entry_point("planner")

    # planner → router
    g.add_edge("planner", "router")

    # router → conditional (tutor/math/reject/__end__)
    g.add_conditional_edges(
        "router",
        route_from_current_subtask,
        {
            "tutor": "tutor",
            "math": "math",
            "reject": "reject",
            "__end__": "feedback",
        },
    )

    # tutor/math loop back to router for next subtask
    g.add_edge("tutor", "router")
    g.add_edge("math", "router")

    # reject → feedback
    g.add_edge("reject", "feedback")

    # Finish at feedback
    g.set_finish_point("feedback")

    return g.compile()
