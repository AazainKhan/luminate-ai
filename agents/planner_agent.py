# agents/planner_agent.py

import json
import os
import re
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception as e:
    print(f"[WARNING] Could not import langchain_google_genai in planner_agent: {e}. LLM features will be disabled for PlannerAgent.")
    ChatGoogleGenerativeAI = None
from langchain_core.prompts import ChatPromptTemplate  

from agents.planner_heuristics import heuristic_route
from prompts.planner_prompts import PLANNER_SYSTEM, PLANNER_USER_FMT
from schemas.planner import (
    PlannerPlan,
    Subtask,
    TaskType,
    ExplainPayload,
    SolvePayload,
    ChatPayload,
    RejectPayload,
)


load_dotenv()


class PlannerAgent:
    """
    LLM-first router with heuristic safety.

    - Always runs heuristics first.
    - Tries LLM plan via Gemini.
    - If LLM succeeds, uses LLM plan, but:
        * Off-topic from heuristics → force reject.
        * If heuristics detect math but LLM forgets a `solve` subtask → append a `solve`.
    - If LLM fails and force_llm=False → fall back to heuristics.
    - If LLM fails and force_llm=True → raise (and caller can decide what to do).
    """

    def __init__(
        self,
        llm: ChatGoogleGenerativeAI,
        enable_llm: bool = True,
        force_llm: bool = True,
        debug: bool = True,
    ) -> None:
        self.llm = llm
        self.enable_llm = enable_llm
        self.force_llm = force_llm
        self.debug = debug

        # Proper ChatPromptTemplate: system + user
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", PLANNER_SYSTEM),
                ("human", PLANNER_USER_FMT),
            ]
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _debug_print_messages(self, messages: List[Any]) -> None:
        """Safe debug printing of formatted messages."""
        if not self.debug:
            return
        print("\n[PlannerAgent] Formatted messages:")
        for i, m in enumerate(messages):
            role = getattr(m, "type", getattr(m, "role", "unknown"))
            content = getattr(m, "content", "")
            print(f"  [{i}] role={role} content[:120]={repr(content[:120])}")
        print()

    def _extract_json_block(self, text: str) -> str:
        """
        Extract the first JSON object from a text blob.
        The LLM is instructed to output **only** JSON, but we’re defensive.
        """
        # Try a naive first: if text already looks like raw JSON.
        text = text.strip()
        if text.startswith("{") and text.endswith("}"):
            return text

        # Otherwise find the first {...} block
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if not match:
            raise ValueError("No JSON object found in LLM output.")
        return match.group(0)

    def _normalize_plan(self, raw: Dict[str, Any]) -> PlannerPlan:
        """
        Convert raw dict from LLM/heuristics into a PlannerPlan Pydantic model.
        This version avoids assuming anything about PayloadType.
        """
        subtasks_raw = raw.get("subtasks", [])
        subtasks: List[Subtask] = []

        for s in subtasks_raw:
            task_str = s.get("task")
            payload_raw = s.get("payload", {}) or {}

            if task_str is None:
                continue

            try:
                task_type = TaskType(task_str)
            except Exception:
                # Unknown task → treat as reject
                task_type = TaskType.REJECT

            # Normalize payloads by task type
            if task_type == TaskType.EXPLAIN:
                # Expect payload like {"topic": "..."}
                if isinstance(payload_raw, dict):
                    payload = ExplainPayload(**payload_raw)
                else:
                    payload = ExplainPayload(topic=str(payload_raw))

            elif task_type == TaskType.SOLVE:
                # Expect payload like {"problem": "..."}
                if isinstance(payload_raw, dict):
                    payload = SolvePayload(**payload_raw)
                else:
                    payload = SolvePayload(problem=str(payload_raw))

            elif task_type == TaskType.CHAT:
                # Expect payload like {"message": "..."}
                if isinstance(payload_raw, dict):
                    payload = ChatPayload(**payload_raw)
                else:
                    payload = ChatPayload(message=str(payload_raw))

            else:
                # Reject payload – be permissive
                if isinstance(payload_raw, dict):
                    payload = RejectPayload(**payload_raw)
                else:
                    payload = RejectPayload(reason=str(payload_raw))

            subtasks.append(Subtask(task=task_type, payload=payload))

        plan = PlannerPlan(
            subtasks=subtasks,
            router_confidence=float(raw.get("router_confidence", 0.5)),
            reasoning=str(raw.get("reasoning", "")),
            rules_triggered=list(raw.get("rules_triggered", [])),
            llm_used=bool(raw.get("llm_used", False)),
        )
        return plan


    # ------------------------------------------------------------------
    # Core LLM planning
    # ------------------------------------------------------------------

    def _llm_plan_raw(self, query: str, context_str: str = "") -> Dict[str, Any]:
        """
        Call Gemini via LangChain Chat model with the planner prompt.
        Returns a raw dict (NOT yet Pydantic).
        """
        if not self.enable_llm:
            raise RuntimeError("LLM is disabled for PlannerAgent.")

        if self.debug:
            print(
                "\n================================================================================"
            )
            print(f"[PlannerAgent] _llm_plan_raw called with query: {query}")
            if context_str:
                print(f"[PlannerAgent] Context provided:\n{context_str[:300]}...")
            print(f"[PlannerAgent] LLM type: {type(self.llm).__name__}\n")
            print("[PlannerAgent] Formatting prompt...")

        # Build the full query with context if available
        if context_str:
            full_query = f"{context_str}\n\nCurrent student message: {query}"
        else:
            full_query = query

        # format **messages**
        messages = self.prompt.format_messages(query=full_query)
        self._debug_print_messages(messages)

        # Call LLM
        result = self.llm.invoke(messages)

        # LangChain ChatGoogleGenerativeAI returns a BaseMessage
        content = getattr(result, "content", str(result))

        if self.debug:
            print("[PlannerAgent] Raw LLM content (first 400 chars):")
            print(content[:400])
            print()

        # Extract JSON block
        json_str = self._extract_json_block(content)

        if self.debug:
            print("[PlannerAgent] Extracted JSON block:")
            print(json_str)
            print()

        data = json.loads(json_str)

        # Ensure subtasks is a list
        if "subtasks" not in data and "task" in data:
            data["subtasks"] = [  # single-task convenience form
                {
                    "task": data["task"],
                    "payload": data.get("payload", {}),
                }
            ]
            data.pop("task", None)
            data.pop("payload", None)

        # Mark LLM usage
        data["llm_used"] = True
        return data

    def _parse_llm_plan(self, llm_raw: Any) -> Optional["PlannerOutput"]:
        """
        Take the raw content returned by _llm_plan_raw (string or LC object),
        extract the JSON block, and normalize it into a PlannerOutput using
        self._normalize_plan.

        This is plugged into plan() where you're currently doing:

            llm_raw = self._llm_plan_raw(query)
            llm_plan = self._parse_llm_plan(llm_raw)
        """
        # 1) If it's already a dict from somewhere, just normalize it
        if isinstance(llm_raw, dict):
            try:
                return self._normalize_plan(llm_raw)
            except Exception as e:
                print(f"[PlannerAgent] _parse_llm_plan: normalize error on dict: {e}")
                return None

        # 2) Unwrap ChatMessage / LC result objects
        if hasattr(llm_raw, "content"):
            text = llm_raw.content
        else:
            text = str(llm_raw)

        # 3) Try to extract a ```json ... ``` block
        match = re.search(r"```json(.*?)```", text, re.DOTALL | re.IGNORECASE)
        if match:
            json_str = match.group(1).strip()
        else:
            # Fallback: grab the first {...} block
            match = re.search(r"\{.*\}", text, re.DOTALL)
            if not match:
                print("[PlannerAgent] _parse_llm_plan: no JSON found in LLM output")
                return None
            json_str = match.group(0).strip()

        print(f"[PlannerAgent] _parse_llm_plan: JSON string to parse:\n{json_str}\n")

        # 4) Parse JSON
        try:
            data = json.loads(json_str)
        except Exception as e:
            print(f"[PlannerAgent] _parse_llm_plan: JSON parse error: {e}")
            return None

        # 5) Use your existing helper to turn the dict into a PlannerOutput
        try:
            return self._normalize_plan(data)
        except Exception as e:
            print(f"[PlannerAgent] _parse_llm_plan: normalize error: {e}")
            return None

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def plan(self, query: str, conversation_history: list = None) -> PlannerPlan:
        """
        FIXED EXECUTION ORDER:
        1. Try LLM plan FIRST (with conversation context)
        2. If LLM fails → try heuristics
        3. If heuristics fail → reject
        """

        print(f"[PlannerAgent] Planning for query: {query}")
        enable_llm = self.enable_llm
        force_llm = self.force_llm
        
        # Build context string from conversation history
        context_str = ""
        if conversation_history and len(conversation_history) > 0:
            context_str = self._build_context_string(conversation_history)
            print(f"[PlannerAgent] Using conversation context ({len(conversation_history)} messages)")

        # -------------------------------
        # STEP 1 — LLM PLAN FIRST
        # -------------------------------
        if enable_llm:
            try:
                print("[PlannerAgent] Trying LLM-first planning...")
                llm_raw = self._llm_plan_raw(query, context_str)
                llm_plan = self._parse_llm_plan(llm_raw)

                if llm_plan:
                    print("[PlannerAgent] LLM plan succeeded")
                    llm_plan.llm_used = True
                    return llm_plan

            except Exception as e:
                print(f"[PlannerAgent] LLM plan failed: {e}")

                # If force_llm = True → fail immediately
                if force_llm:
                    raise Exception("Planner failed: LLM plan failed and force_llm is True")

                print("[PlannerAgent] Falling back to heuristic rules...")

        # -------------------------------
        # STEP 2 — HEURISTIC PLAN
        # -------------------------------
        try:
            heuristic = self._heuristic_plan(query)
            if heuristic:
                print("[PlannerAgent] Heuristic plan used")
                heuristic.llm_used = False
                return heuristic
        except Exception as e:
            print(f"[PlannerAgent] ERROR in heuristic planning: {e}")

        # -------------------------------
        # STEP 3 — FINAL FALLBACK → reject task
        # -------------------------------
        print("[PlannerAgent] Both LLM and heuristics failed → defaulting to REJECT")
        return PlannerOutput(
            subtasks=[
                Subtask(task=TaskType.CHAT, payload={"message": "off_topic"})
            ],
            router_confidence=0.0,
            reasoning="Planner failed: no valid route found",
            rules_triggered=["planner_error"],
            llm_used=False
        )
    
    def _build_context_string(self, conversation_history: list) -> str:
        """Build a context string from conversation history for the planner."""
        if not conversation_history:
            return ""
        
        lines = ["Recent conversation context:"]
        # Only use last few messages for context
        recent = conversation_history[-6:] if len(conversation_history) > 6 else conversation_history
        
        for msg in recent:
            role = msg.get("role", "unknown")
            content = msg.get("content", "")
            if role == "student":
                lines.append(f"Student: {content}")
            elif role == "assistant":
                # Truncate long assistant responses
                content_short = content[:200] + "..." if len(content) > 200 else content
                lines.append(f"Tutor: {content_short}")
        
        return "\n".join(lines)
