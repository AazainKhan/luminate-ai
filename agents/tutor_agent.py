
"""
tutor_agent.py - Production TutorAgent with Direct ChromaDB Access + Scope Guard

- Uses ChromaDB directly (same as ingestion scripts)
- Enforces COMP237 scope: if no relevant COMP237 chunks, only a one-line high-level answer
- Adds a simple "Sources used" section based on retrieved chunks
"""

from __future__ import annotations

import os
import textwrap
from typing import Dict, List, Any, Tuple

import chromadb
from chromadb.config import Settings

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from config.chroma_config import CHROMA_SETTINGS


# ---------------------------------------------------------------------------
# RAG RETRIEVER
# ---------------------------------------------------------------------------

class DirectRAGRetriever:
    """
    Simple, explicit ChromaDB retriever that:
    - Reads from persistent ./chroma_db
    - Queries both course_comp237 and oer_resources
    - Returns structured docs with a crude similarity score
    """

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory

        os.makedirs(self.persist_directory, exist_ok=True)
        print(f"[RAG] Ensuring ChromaDB directory exists at: {self.persist_directory}")

        # IMPORTANT FIX: CHROMA_SETTINGS is already a Settings object
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=CHROMA_SETTINGS  # Don't wrap with Settings(...)
        )

        try:
            collections = self.client.list_collections()
            names = [c.name for c in collections]
        except Exception:
            names = []
        print(f"[RAG] Available collections: {names}")


    def _query_collection(
        self,
        collection_name: str,
        query: str,
        top_k: int,
    ) -> List[Dict[str, Any]]:
        try:
            col = self.client.get_collection(collection_name)
        except Exception as e:
            print(f"[RAG] Failed to load collection '{collection_name}': {e}")
            return []

        print(f"[RAG] Loaded collection '{collection_name}'")
        res = col.query(
            query_texts=[query],
            n_results=top_k,
            include=["documents", "metadatas", "distances"],
        )

        docs: List[Dict[str, Any]] = []
        docs_raw = res.get("documents", [[]])[0]
        metas_raw = res.get("metadatas", [[]])[0]
        dists_raw = res.get("distances", [[]])[0]

        for doc, meta, dist in zip(docs_raw, metas_raw, dists_raw):
            # Turn distance into a crude "similarity" score in (0, 1]
            # Higher = more similar
            score = 1.0 / (1.0 + float(dist)) if dist is not None else 0.0
            docs.append(
                {
                    "content": doc,
                    "metadata": meta or {},
                    "collection": collection_name,
                    "score": score,
                }
            )

        print(f"[RAG] {collection_name}: Retrieved {len(docs)} documents")
        return docs

    def retrieve_context(
        self,
        query: str,
        top_k: int = 3,
        comp237_threshold: float = 0.35,
    ) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
        """
        Retrieve context from both course_comp237 and oer_resources.

        Returns:
            (docs, rag_metadata)
        """
        all_docs: List[Dict[str, Any]] = []

        # Query both collections
        for name in ["course_comp237", "oer_resources"]:
            all_docs.extend(self._query_collection(name, query, top_k))

        print(f"[RAG] Total retrieved: {len(all_docs)} documents")

        # Split by collection for gating
        comp_docs = [
            d for d in all_docs
            if d.get("collection") == "course_comp237"
            and d.get("score", 0.0) >= comp237_threshold
        ]
        oer_docs = [d for d in all_docs if d.get("collection") == "oer_resources"]

        has_comp237 = len(comp_docs) > 0

        # If we have comp237 docs, keep them + optionally some OER for extra color
        if has_comp237:
            used_docs = comp_docs + oer_docs
        else:
            # Only OER docs are meaningfully similar, treat as out-of-scope
            used_docs = oer_docs

        rag_metadata = {
            "docs_retrieved": len(used_docs),
            "sources_used": sorted({d.get("collection") for d in used_docs}),
            "retrieval_success": len(used_docs) > 0,
            "has_comp237": has_comp237,
        }

        print(
            f"[RAG] Successfully retrieved {len(used_docs)} documents | "
            f"has_comp237={has_comp237} | sources={rag_metadata['sources_used']}"
        )

        return used_docs, rag_metadata


# ---------------------------------------------------------------------------
# PROMPTS
# ---------------------------------------------------------------------------

# In-scope teaching prompt (COMP237 context available)
TUTOR_IN_SCOPE_PROMPT = ChatPromptTemplate.from_template(
    textwrap.dedent(
        """
        You are a **course-aligned AI tutor** for COMP237 (Intro to AI).
        You MUST teach using the provided course context.

        MODE: {mode}

        ORIGINAL STUDENT QUESTION:
        {student_question}

        STUDENT TOPIC (aligned with planner):
        {topic}

        COURSE CONTEXT (from COMP237 + OER):
        {context}

        YOUR TASK:
        - Give a clear, step-by-step teaching explanation.
        - Start from intuition, then move to definitions, then examples.
        - Reference course ideas naturally (e.g., "earlier in the course we saw...").
        - DO NOT invent new content not supported by the context.
        - If something is not in the context, you may give a light, high-level note
          but mark it clearly as **beyond what is shown here**.

        STRUCTURE YOUR ANSWER AS:

        1. **Big picture overview** (2–4 sentences).
        2. **Core concepts** in bullet points.
        3. **Step-by-step reasoning or walkthrough** if applicable.
        4. **Quick check for understanding** (2–3 questions).
        5. **Summary** (2–3 bullet points).
        6. **Sources used (by collection)**:
           - List which parts of the explanation came from `course_comp237`
             vs `oer_resources`. Keep this as bullet points like:
             - `[COURSE] ...`
             - `[OER] ...`

        IMPORTANT:
        - Think through the explanation carefully and keep it consistent with the context.
        - Do NOT say that you are using RAG or ChromaDB.

        LENGTH & STYLE RULES:
        1. If MODE == "short":
        - The student explicitly asked for a brief answer (e.g., "in 2 lines", "briefly").
        - You MUST obey their requested length/format, even if course context is available.
        - If the question says "in 2 lines":
            - Respond with AT MOST 2 sentences.
            - Do NOT add headings, bullet points, lists, or extra blank lines.
            - Just write 1–2 concise sentences of plain text.
        - If the question says "one line" or "1 line":
            - Respond with exactly ONE concise sentence.
        - If the question just says "briefly" or "short answer" without a line count:
            - Respond with 2–3 short sentences maximum.

        2. If MODE == "full":
        - Use structured, teaching-style output with sections, examples, and checks for understanding.
        - You may use headings, bullet points, and multiple paragraphs.
        - Do NOT mention MODE, line counts, or these rules explicitly in your answer.
        
        """)     
)


# Out-of-scope prompt (no COMP237 match)
TUTOR_OOS_PROMPT = ChatPromptTemplate.from_template(
    textwrap.dedent(
        """
        You are a strict COMP237 tutor.

        The student's question was:
        {question}

        The course RAG retriever did NOT find any relevant COMP237 material
        for this topic.

        TASK:
        - First line: say clearly that this topic is outside the official scope of COMP237.
        - Second line: give ONLY ONE short, high-level sentence (max 25 words)
          giving a general idea of what it is.
        - Do NOT provide details, derivations, long explanations, or examples.
        - Do NOT reference any course sections or textbooks by name.

        Format exactly:

        This topic is outside the official scope of COMP237.
        <one concise sentence here>
        """
    )
)


# ---------------------------------------------------------------------------
# Helper to format context into a readable block
# ---------------------------------------------------------------------------


def format_context(docs: List[Dict[str, Any]], max_chars: int = 4000) -> str:
    """
    Turn retrieved docs into a single context string with lightweight
    inline "citations" indicating collection and (optionally) a title/id.
    """
    pieces = []
    total_len = 0

    for i, d in enumerate(docs):
        coll = d.get("collection", "unknown")
        meta = d.get("metadata") or {}
        title = meta.get("title") or meta.get("source_id") or f"doc_{i+1}"
        content = (d.get("content") or "").strip()

        header = f"[{coll.upper()} :: {title}]"
        block = f"{header}\n{content}\n"
        block_len = len(block)

        if total_len + block_len > max_chars:
            break

        pieces.append(block)
        total_len += block_len

    if not pieces:
        return "No course context could be formatted."

    return "\n\n".join(pieces)


# ---------------------------------------------------------------------------
# MAIN ENTRYPOINT: tutor_node
# ---------------------------------------------------------------------------

def tutor_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    This function is called by graph_ai._call_tutor.

    Expected input `state` (from graph_ai):
        {
            "student_input": <str>,        # original question/topic
            "plan": {"topic": <str>},      # planner-decided topic
            "conversation": <full graph state>   # (we ignore)
        }

    Returns a dict like:
        {
            "tutor_response": <str>,
            "rag_metadata": {...},
            "is_fallback_response": <bool>
        }
    """
    print("\n" + "=" * 70)
    print("[TutorAgent] tutor_node called")
    print(f"[TutorAgent] Incoming state keys: {list(state.keys())}")

    raw_question = state.get("student_input", "") or ""
    plan = state.get("plan", {}) or {}
    topic = plan.get("topic") or raw_question

    # ----------------------------------------------------------------------
    # NEW: detect "mode" (short vs full) from the original student question
    # ----------------------------------------------------------------------
    student_question_str = str(raw_question or topic)
    q_lower = student_question_str.lower()

    short_triggers = [
        "in 2 lines",
        "in two lines",
        "one line",
        "1 line",
        "briefly",
        "short answer",
        "in short",
    ]

    mode = "full"
    for trig in short_triggers:
        if trig in q_lower:
            mode = "short"
            break

    print(f"[TutorAgent] Processing Topic: {topic} | mode={mode}")

    rag_metadata: Dict[str, Any] = {
        "docs_retrieved": 0,
        "sources_used": [],
        "retrieval_success": False,
        "has_comp237": False,
    }

    try:
        # 1) RAG – ChromaDB
        retriever = DirectRAGRetriever(persist_directory="./chroma_db")
        docs, rag_metadata = retriever.retrieve_context(topic, top_k=3)

        # 2) LLM setup
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            temperature=0.3,
        )

        # 3) If no COMP237 context → out-of-scope short answer
        if not rag_metadata.get("has_comp237", False):
            print("[TutorAgent] No COMP237 context found → out-of-scope mode.")
            # You can update TUTOR_OOS_PROMPT later to optionally use `mode`
            messages = TUTOR_OOS_PROMPT.format_messages(
                question=student_question_str,
                mode=mode,                 # extra kwargs are ignored if not used in template
                student_question=student_question_str,
                topic=topic,
            )
            result = llm.invoke(messages)
            text = (result.content or "").strip()

            return {
                "tutor_response": text,
                "rag_metadata": rag_metadata,
                "is_fallback_response": False,
            }

        # 4) In-scope: teaching explanation with COMP237 context
        print("[TutorAgent] COMP237 context found → in-scope teaching mode.")
        context_str = format_context(docs)

        # IMPORTANT: your TUTOR_IN_SCOPE_PROMPT template must now have
        # {mode}, {student_question}, {topic}, {context} placeholders.
        messages = TUTOR_IN_SCOPE_PROMPT.format_messages(
            mode=mode,
            student_question=student_question_str,
            topic=topic,
            context=context_str,
        )
        result = llm.invoke(messages)
        text = (result.content or "").strip()

        print(f"[TutorAgent] Generated response length: {len(text)} chars")

        return {
            "tutor_response": text,
            "rag_metadata": rag_metadata,
            "is_fallback_response": False,
        }

    except Exception as e:
        print(f"[TutorAgent] ERROR in tutor_node: {e}")
        import traceback
        traceback.print_exc()

        # best-effort fallback
        return {
            "tutor_response": (
                "I ran into a problem while answering your question. "
                "Please try again, or rephrase your question."
            ),
            "rag_metadata": rag_metadata,
            "is_fallback_response": True,
        }
