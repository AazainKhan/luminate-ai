# main.py
import os, uuid
from typing import Any, Dict
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# Agents & tools
from agents.planner_agent import PlannerAgent
import agents.tutor_agent as tutor_mod            # state-based tutor module
from agents.math_agent import MathAgent
from tools.rag_tool import RagTool
from tools.math_tool import MathTool

# LLM
from langchain_google_genai import ChatGoogleGenerativeAI

# Feedback + Postgres logging
from agents.feedback_agent import FeedbackAgent
from tools.db import log_message, save_rating, get_conversation_history

# Graph
from graph.graph_ai import build_ai_tutor_graph

load_dotenv()

# In-memory conversation history fallback (when PostgreSQL isn't available)
from collections import defaultdict, deque
conversation_memory: Dict[str, deque] = defaultdict(lambda: deque(maxlen=20))

# ---------- shared LLM & tools ----------

# main.py
from langchain_google_genai import ChatGoogleGenerativeAI
from agents.planner_agent import PlannerAgent
import os

os.environ.setdefault("GOOGLE_API_KEY", "AIzaSyDldXJV7TQ75UYCIAkg2kIkr7rWETAxMDw")  # or .env
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", temperature=0.2, max_output_tokens=1024)

planner_agent = PlannerAgent(llm=llm, enable_llm=True, force_llm=True)

rag = RagTool(persist_dir="./chroma_db")   # update if your index folder differs
math_tool = MathTool()

# ---------- agents ----------
# planner_agent = PlannerAgent(llm, enable_llm=bool(llm))
planner_agent = PlannerAgent(llm=llm, enable_llm=True, force_llm=True)
tutor_agent   = tutor_mod                   # module; we call into it from the graph
math_agent    = MathAgent(rag, math_tool, llm)
feedback_agent = FeedbackAgent()            # optional for /feedback/run

# ---------- graph ----------
graph = build_ai_tutor_graph(planner_agent, tutor_agent, math_agent)

# ---------- FastAPI ----------
app = FastAPI(title="Luminate AI Tutor")

# Add CORS middleware to allow Chrome extension to connect
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify your extension ID
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ----- request models -----
class Ask(BaseModel):
    question: str
    conversation_id: str | None = None
    turn_index: int | None = None

class Rate(BaseModel):
    conversation_id: str
    rating: int  # 1..5

# ----- endpoints -----
def safe_serialize(obj):
    """Safely serialize objects that might contain non-serializable data"""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {k: safe_serialize(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [safe_serialize(item) for item in obj]
    if hasattr(obj, 'model_dump'):
        return safe_serialize(obj.model_dump())
    if hasattr(obj, 'dict'):
        return safe_serialize(obj.dict())
    try:
        return str(obj)
    except Exception:
        return "[unserializable object]"

@app.post("/ask")
def ask(body: Ask):
    try:
        # 1) assign/use conversation id + turn index
        cid = body.conversation_id or str(uuid.uuid4())
        turn = 0 if body.turn_index is None else int(body.turn_index)
        print(f"\n{'='*50}")
        print(f"[ask] New request - CID: {cid}, Turn: {turn}")
        print(f"[ask] Question: {body.question}")

        # 2) log student turn (Postgres) - make optional if DB not available
        try:
            log_message(cid, turn, "student", body.question, agent="PlannerAgent")
        except Exception as e:
            print(f"[WARNING] Could not log to database: {e}")
        
        # Also store in memory
        conversation_memory[cid].append({
            "turn_index": turn,
            "role": "student",
            "content": body.question
        })

        # 2.5) retrieve conversation history (try DB first, fallback to memory)
        conversation_history = []
        try:
            conversation_history = get_conversation_history(cid, limit=10)
            if conversation_history:
                print(f"[ask] Retrieved {len(conversation_history)} previous messages from DB")
        except Exception as e:
            print(f"[WARNING] Could not retrieve from database: {e}, using in-memory history")
            # Fallback to in-memory history
            conversation_history = list(conversation_memory[cid])
            if conversation_history:
                print(f"[ask] Using {len(conversation_history)} messages from memory")

        # 3) run graph: planner → (tutor/math)* → feedback/reject
        state: Dict[str, Any] = {
            "student_input": body.question,
            "conversation_id": cid,
            "turn_index": turn,
            "conversation_history": conversation_history,
        }
        
        print("[ask] Invoking graph...")
        result = graph.invoke(state)
        print(f"[ask] Graph execution completed. Result keys: {list(result.keys())}")
        
        # Debug: Print the full result structure (truncated)
        print("\n[ask] Full result structure:")
        for key, value in result.items():
            value_str = str(value)
            print(f"  {key}: {value_str[:200]}{'...' if len(value_str) > 200 else ''}")

        # ------------------------------------------------------------------
        # NEW: build a CLEAR combined assistant_response from plan + outputs
        # ------------------------------------------------------------------
        plan = result.get("plan") or {}
        outputs_list = result.get("outputs") or []
        routing_info = result.get("routing_info") or {}
        node_processing = result.get("node_processing") or {}
        rag_metadata = result.get("rag_metadata") or {}

        subtasks = plan.get("subtasks") or []

        # Collect responses without adding extra formatting headers
        combined_sections: List[str] = []

        if subtasks and outputs_list:
            # Pair each subtask with the corresponding outputs[i]
            for i, sub in enumerate(subtasks):
                response_text = ""
                if i < len(outputs_list):
                    response_text = outputs_list[i].get("response", "") or ""
                if response_text.strip():
                    # Just use the response text directly - no === headers ===
                    combined_sections.append(response_text.strip())
        elif outputs_list:
            # Fallback: just combine whatever responses we have
            for i, out in enumerate(outputs_list):
                response_text = out.get("response", "") or ""
                if response_text.strip():
                    combined_sections.append(response_text.strip())
        else:
            # Last fallback: use `result["output"]` if present
            fallback = result.get("output", "") or ""
            if str(fallback).strip():
                combined_sections.append(str(fallback).strip())

        # Final combined assistant message - just the clean response text
        assistant_response = "\n\n".join(combined_sections) if combined_sections else ""

        # 4) log compact assistant turn - make optional if DB not available
        try:
            assistant_summary = assistant_response[:2000]
            log_message(cid, turn + 1, "assistant", assistant_summary, agent="Tutor/Math")
            print(f"[ask] Logged assistant response: {assistant_summary[:100]}...")
        except Exception as e:
            print(f"[WARNING] Could not log to database: {e}")

        # 5) prepare response - ensure all data is serializable
        response = {
            "conversation_id": cid,
            "output": safe_serialize(assistant_response),           # <-- CLEAR combined text
            "student_input": safe_serialize(result.get("student_input")),
            "plan": safe_serialize(plan),
            "outputs": safe_serialize(outputs_list),
            "rag_metadata": safe_serialize(rag_metadata),
            "is_fallback_response": safe_serialize(result.get("is_fallback_response", False)),
            "routing_info": safe_serialize(routing_info),
            "node_processing": safe_serialize(node_processing),
            "status": "success",
        }
        
        # Debug: Print routing and node info
        if "routing_info" in result:
            print(f"[ask] Routing info: {result['routing_info']}")
        if "node_processing" in result:
            print(f"[ask] Node processing: {result['node_processing']}")
        
        # 6) return the safe response
        print(f"[ask] Sending response. Output length: {len(str(assistant_response))}")
        print(f"[ask] Response keys: {list(response.keys())}")
        print(f"[ask] Response output type: {type(assistant_response)}")
        print(f"[ask] First 100 chars of output: {str(assistant_response)[:100]}")
        print(f"{'='*50}\n")

        return response

    except Exception as e:
        import traceback
        error_details = f"Error in /ask endpoint: {str(e)}\n{traceback.format_exc()}"
        print(error_details)  # Log the full error for debugging
        return {
            "conversation_id": body.conversation_id if hasattr(body, "conversation_id") else "unknown",
            "error": "An error occurred while processing your request",
            "status": "error",
            "details": str(e)[:500],  # Include first 500 chars of error message
        }


# @app.post("/ask")
# def ask(body: Ask):
#     try:

#         # 1) assign/use conversation id + turn index
#         cid = body.conversation_id or str(uuid.uuid4())
#         turn = 0 if body.turn_index is None else int(body.turn_index)
#         print(f"\n{'='*50}")
#         print(f"[ask] New request - CID: {cid}, Turn: {turn}")
#         print(f"[ask] Question: {body.question}")

#         # 2) log student turn (Postgres)
#         log_message(cid, turn, "student", body.question, agent="PlannerAgent")

#         # 3) run graph: planner → (tutor/math)* → feedback/reject
#         state: Dict[str, Any] = {
#             "student_input": body.question,
#             "conversation_id": cid,
#             "turn_index": turn
#         }
        
#         print("[ask] Invoking graph...")
#         result = graph.invoke(state)
#         print(f"[ask] Graph execution completed. Result keys: {list(result.keys())}")
        
#         # Debug: Print the full result structure
#         print("\n[ask] Full result structure:")
#         for key, value in result.items():
#             value_str = str(value)
#             print(f"  {key}: {value_str[:200]}{'...' if len(value_str) > 200 else ''}")

#         # 4) log compact assistant turn
#         assistant_response = result.get("output", "")
#         assistant_summary = str(assistant_response)[:2000]
#         log_message(cid, turn + 1, "assistant", assistant_summary, agent="Tutor/Math")
#         print(f"[ask] Logged assistant response: {assistant_summary[:100]}...")

#         # 5) prepare response - ensure all data is serializable
#         response = {
#             "conversation_id": cid,
#             "output": safe_serialize(assistant_response),
#             "student_input": safe_serialize(result.get("student_input")),
#             "plan": safe_serialize(result.get("plan")),
#             "outputs": safe_serialize(result.get("outputs", [])),
#             "rag_metadata": safe_serialize(result.get("rag_metadata", {})),
#             "is_fallback_response": safe_serialize(result.get("is_fallback_response", False)),
#             "routing_info": safe_serialize(result.get("routing_info", {})),
#             "node_processing": safe_serialize(result.get("node_processing", {})),
#             "status": "success"
#         }
        
#         # Debug: Print routing and node info
#         if "routing_info" in result:
#             print(f"[ask] Routing info: {result['routing_info']}")
#         if "node_processing" in result:
#             print(f"[ask] Node processing: {result['node_processing']}")
        
#         # 6) return the safe response
#         print(f"[ask] Sending response. Output length: {len(str(assistant_response))}")
#         print(f"[ask] Response keys: {list(response.keys())}")
#         print(f"[ask] Response output type: {type(assistant_response)}")
#         print(f"[ask] First 100 chars of output: {str(assistant_response)[:100]}")
#         print(f"{'='*50}\n")

        
#         return response

        
        
#     except Exception as e:
#         import traceback
#         error_details = f"Error in /ask endpoint: {str(e)}\n{traceback.format_exc()}"
#         print(error_details)  # Log the full error for debugging
#         return {
#             "conversation_id": body.conversation_id if hasattr(body, 'conversation_id') else "unknown",
#             "error": "An error occurred while processing your request",
#             "status": "error",
#             "details": str(e)[:500]  # Include first 500 chars of error message
#         }

@app.post("/rate")
def rate(body: Rate):
    save_rating(body.conversation_id, int(body.rating))
    return {"status": "ok"}

@app.post("/feedback/run")
def feedback_run():
    # Try FeedbackAgent's batch methods if present
    try:
        if hasattr(feedback_agent, "run_weekly"):
            out = feedback_agent.run_weekly()
            return {"status": "ok", "source": "FeedbackAgent.run_weekly", "output": out}
        if hasattr(feedback_agent, "analyze_recent"):
            out = feedback_agent.analyze_recent()
            return {"status": "ok", "source": "FeedbackAgent.analyze_recent", "output": out}
    except Exception as e:
        fallback_err = f"FeedbackAgent failed: {e}"

    # Fallback to the job script under tools/
    try:
        from tools import run_feedback_job as job
        if hasattr(job, "main"):
            out = job.main()
            return {"status": "ok", "source": "run_feedback_job.main", "output": out}
    except Exception as e:
        return {"status": "error", "message": f"{fallback_err if 'fallback_err' in locals() else ''} | job error: {e}"}

    return {"status": "error", "message": "No callable feedback job found"}
