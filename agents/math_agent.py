from typing import List, Dict, Any, Tuple, Optional
import re

from pydantic import ValidationError
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from schemas.math import MathTask, MathAgentOutput, Step, Source, ComputationResult
from tools.rag_tool import RagTool
from tools.math_tool import MathTool
from prompts.math_prompts import TUTOR_MATH_SYSTEM, TUTOR_MATH_INSTRUCTIONS

DEFAULT_MAX_WORDS = 700


def _expand_queries(q: str) -> List[str]:
    """
    Lightly expand a math query for retrieval.
    """
    q = q.strip()
    return [
        q,
        f"{q} example",
        f"{q} formula",
        f"{q} step by step",
        f"how to {q}",
    ]


class MathAgent:
    """
    MathAgent: orchestrates RAG + MathTool + LLM teaching for 'solve' tasks.
    """

    def __init__(self, rag: RagTool, math: MathTool, llm: ChatGoogleGenerativeAI):
        self.rag = rag
        self.math = math
        self.llm = llm
        self.prompt = ChatPromptTemplate.from_messages(
            [
                ("system", TUTOR_MATH_SYSTEM),
                ("human", TUTOR_MATH_INSTRUCTIONS),
            ]
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _normalize_problem(self, problem: str) -> Dict[str, Any]:
        """
        Normalize a raw user math problem into something MathTool can safely consume.

        - Strips leading verbs like 'solve', 'compute', 'find', etc.
        - Converts patterns like:
              '3x + y = 12 for y = 1'
          into a SymPy-friendly multi-part prompt:
              '3x + y = 12; y = 1'
          so that MathTool._sympy() can treat the second part as a substitution
          instead of trying to parse 'for' (which is a Python keyword).

        Returns a dict:
            {
              'original_problem': ...,
              'clean_problem': ...,
              'compute_prompt': ...,
              'topic_hint': ...,
              'substitutions': {...}
            }
        """
        original = (problem or "").strip()
        clean = original

        # Strip common leading verbs that confuse parsers but aren't needed
        for verb in ["solve", "compute", "calculate", "find", "evaluate", "determine"]:
            clean = re.sub(rf"^\s*{verb}\s+", "", clean, flags=re.IGNORECASE)

        substitutions: Dict[str, str] = {}

        # Handle simple "for y = 1" style clauses
        # e.g. "3x + y = 12 for y = 1" -> "3x + y = 12; y = 1"
        compute_prompt = clean
        m = re.search(r"\bfor\b(.+)", clean, flags=re.IGNORECASE)
        if m:
            main_part = clean[: m.start()].strip()
            tail = m.group(1).strip()
            if "=" in tail:
                # keep only the algebraic part in the compute prompt
                compute_prompt = f"{main_part}; {tail}"
                # also parse substitutions dictionary for future scaffolding / checking
                for piece in tail.split(","):
                    if "=" in piece:
                        var, val = piece.split("=", 1)
                        substitutions[var.strip()] = val.strip()

        topic_hint: Optional[str] = None
        # Very light heuristic: if the problem mentions a named topic, surface it
        for keyword in [
            "derivative",
            "integral",
            "limit",
            "probability",
            "matrix",
            "linear regression",
            "regression",
            "system of equations",
        ]:
            if keyword.lower() in original.lower():
                topic_hint = keyword
                break

        return {
            "original_problem": original,
            "clean_problem": clean,
            "compute_prompt": compute_prompt,
            "topic_hint": topic_hint,
            "substitutions": substitutions,
        }

    def _retrieve(self, q: str, k: int = 6) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a math query using RagTool.

        We:
        - Try the original query
        - If results are weak, try some expanded variants
        - Deduplicate by (text, collection) pairs
        """
        print("[MathAgent] RAG retrieving for query:", q)
        hits: List[Dict[str, Any]] = []

        try:
            hits.extend(self.rag.retrieve(q, k=k))
        except Exception as e:
            print(f"[MathAgent] Error during initial retrieve: {e}")

        # If we didn't get enough, try expansions
        if len(hits) < k:
            seen = {(h.get("text"), (h.get("meta") or {}).get("collection")) for h in hits}
            for alt in _expand_queries(q)[1:]:
                if len(hits) >= k:
                    break
                try:
                    more = self.rag.retrieve(alt, k=max(2, k // 2))
                except Exception as e:
                    print(f"[MathAgent] Error during expanded retrieve '{alt}': {e}")
                    continue
                for h in more:
                    key = (h.get("text"), (h.get("meta") or {}).get("collection"))
                    if key in seen:
                        continue
                    hits.append(h)
                    seen.add(key)

        print(f"[MathAgent] Retrieved {len(hits)} context docs")
        return hits[:k]

    def _build_context_and_sources(
        self, docs: List[Dict[str, Any]]
    ) -> Tuple[str, List[Source]]:
        """
        Turn RAG docs into:
        - a big context string fed to the LLM
        - a list of Source objects for structured output
        """
        if not docs:
            return "", []

        context_chunks: List[str] = []
        sources: List[Source] = []

        for idx, d in enumerate(docs, start=1):
            text = d.get("text") or d.get("document") or ""
            meta = d.get("meta") or d.get("metadata") or {}
            collection = meta.get("collection") or meta.get("source") or "unknown"
            marker = f"†{idx}"

            # Context chunk (what the LLM sees)
            context_chunks.append(f"[{marker}] {text}")

            # Structured source object (what we log/return)
            sources.append(
                Source(
                    marker=marker,
                    collection=collection,
                    metadata=meta,
                )
            )

        context = "\n\n".join(context_chunks)
        return context, sources

    def _summarise_compute(self, compute_res: Optional[Dict[str, Any]]) -> str:
        """
        Turn a MathTool result dict into a short string injected into the prompt.
        """
        if not compute_res:
            return "No external computation tool was successfully used."

        tool = compute_res.get("tool", "unknown")
        inp = compute_res.get("input", "")
        txt = compute_res.get("result_text", "")
        return f"Tool: {tool}\nInput: {inp}\nResult: {txt}"

    def _extract_answer(self, txt: str) -> str:
        """
        Pull out a reasonably concise 'final answer' line from the LLM text.

        This is heuristic and you can improve it later.
        """
        for block in txt.split("\n\n"):
            if "final answer" in block.lower():
                # first non-empty line after the phrase
                lines = [l.strip() for l in block.splitlines() if l.strip()]
                if lines:
                    return lines[0]
        # fall back to first line
        first_line = txt.strip().splitlines()[0] if txt.strip() else ""
        return first_line

    # ------------------------------------------------------------------
    # Public entry-point used by graph_ai._call_math
    # ------------------------------------------------------------------
    def math_node(self, request: Dict[str, Any]) -> MathAgentOutput:
        """
        Entry point used by the LangGraph math_node wrapper.

        Expects:
            request = {"problem": "..."}
        """
        problem = (request or {}).get("problem", "") or ""
        print(f"[MathAgent] math_node called with problem: {problem!r}")

        # 1) Normalise the problem so the compute layer doesn't choke on 'for'
        norm = self._normalize_problem(problem)
        compute_prompt = norm["compute_prompt"]
        topic_hint = norm["topic_hint"] or "math problem"

        # 2) Retrieve RAG context (always on for MathAgent)
        docs = self._retrieve(problem)
        context, sources = self._build_context_and_sources(docs)

        # 3) Run MathTool (Wolfram → SymPy). If Wolfram is not configured
        #    (no WOLFRAM_APP_ID), MathTool falls back to SymPy.
        compute_res: Optional[Dict[str, Any]] = None
        if compute_prompt:
            try:
                compute_res = self.math.compute(compute_prompt)
            except Exception as e:
                print(f"[MathAgent] Error in MathTool.compute: {e}")
                compute_res = None

        compute_summary = self._summarise_compute(compute_res)

        # 4) Ask the LLM to explain + teach
        try:
            messages = self.prompt.format_messages(
                max_words=DEFAULT_MAX_WORDS,
                problem=problem,
                topic=topic_hint,
                level="college",
                precision=4,
                context=context,
                compute_summary=compute_summary,
            )
            llm_resp = self.llm.invoke(messages)
            explanation = getattr(llm_resp, "content", str(llm_resp))
        except Exception as e:
            # If the LLM call fails, still return a structured error object
            print(f"[MathAgent] LLM call failed: {e}")
            raise

        final_answer = self._extract_answer(explanation)

        # 5) Build structured MathAgentOutput
        try:
            out = MathAgentOutput(
                final_answer=final_answer,
                final_answer_latex=None,  # You can add LaTeX extraction later
                steps=[
                    Step(
                        title="Solution",
                        text=explanation,
                    )
                ],
                concepts_used=[],
                sources=sources,
                computation=ComputationResult(**compute_res)
                if compute_res
                else None,
                needs_clarification=False,  # prompt already asks to surface ambiguity
                clarifying_questions=[],
                confidence=0.7 if compute_res else 0.6,
            )
        except ValidationError as ve:
            # If validation fails, wrap explanation in a minimal valid payload
            print(f"[MathAgent] ValidationError building MathAgentOutput: {ve}")
            out = MathAgentOutput(
                final_answer=final_answer or "See explanation.",
                final_answer_latex=None,
                steps=[
                    Step(
                        title="Solution",
                        text=explanation,
                    )
                ],
                concepts_used=[],
                sources=sources,
                computation=None,
                needs_clarification=False,
                clarifying_questions=[],
                confidence=0.5,
                notes=f"Validation error: {ve}",
            )
        return out
