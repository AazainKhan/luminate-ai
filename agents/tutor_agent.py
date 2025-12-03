
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

try:
    from langchain_google_genai import ChatGoogleGenerativeAI
except Exception as e:
    print(f"[WARNING] Could not import langchain_google_genai in tutor_agent: {e}. LLM features may be degraded.")
    ChatGoogleGenerativeAI = None
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

# In-scope teaching prompt with SCAFFOLDING pedagogy (COMP237 context available)
TUTOR_IN_SCOPE_PROMPT = ChatPromptTemplate.from_template(
    textwrap.dedent(
        """
        You are a **Socratic AI tutor** for COMP237 (Intro to AI).
        Your PRIMARY goal is to help students DISCOVER answers through hints and questions.
        
        ⚠️ CRITICAL: ESCALATION LEVEL = {escalation_level}
        
        **RESPOND BASED ON ESCALATION LEVEL:**
        
        🔹 If ESCALATION_LEVEL = 1 (HINTS ONLY - No examples yet!):
        → DO NOT give examples like "think of a thermostat" or "like a Roomba"
        → DO NOT explain the concept directly
        → ONLY ask thought-provoking questions to make them think
        → Format: "Great question! Let me ask you something first: [guiding question]? What do you think?"
        → Keep it SHORT (2-3 sentences max)
        
        Example Level 1 response for "What is an agent in AI?":
        "Great question! Before I explain, let me ask you: In everyday life, what does an 'agent' do? Think about a real estate agent or a travel agent - what's their main job? How might that relate to AI?"
        
        🔹 If ESCALATION_LEVEL = 2 (More specific hint):
        → Give a more directed hint that points toward the answer
        → Can mention a simple analogy but still ask a question
        → Format: "Here's a hint: [analogy]. What does that suggest about [topic]?"
        
        🔹 If ESCALATION_LEVEL = 3 (Concrete example needed):
        → NOW provide a concrete example (thermostat, Roomba, etc.)
        → Walk through the example step by step
        → Ask: "Does this example help? Which part is unclear?"
        
        🔹 If ESCALATION_LEVEL = 4 (Full explanation):
        → STOP asking questions!
        → Give a CLEAR, DIRECT explanation (2-3 paragraphs)
        → Include a concrete example
        → End with: "Does this make sense now?"

        MODE: {mode}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        📜 CONVERSATION HISTORY:
        {history}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        CURRENT STUDENT MESSAGE:
        {student_question}

        TOPIC BEING DISCUSSED:
        {topic}

        COURSE CONTEXT (from COMP237 + OER):
        {context}
        
        📝 FORMATTING REQUIREMENTS:
        - Use double newlines between paragraphs
        - Keep paragraphs SHORT (2-3 sentences max)
        - Use **bold** for key terms sparingly
        - NEVER write walls of text
        
        ⚠️ CRITICAL RULES:
        - DO NOT show "ESCALATION_LEVEL" or reasoning in your response
        - Just respond naturally based on the level
        - LEVEL 1 = ONLY QUESTIONS, NO EXAMPLES
        - If level is 4, give a clear explanation - don't keep asking questions!
        - Match the escalation level exactly!
        
        YOUR RESPONSE (based on escalation level {escalation_level}):
        """
    )
)


# Out-of-scope prompt (no COMP237 match) - still encourage thinking
TUTOR_OOS_PROMPT = ChatPromptTemplate.from_template(
    textwrap.dedent(
        """
        You are a scaffolding-based COMP237 AI tutor.

        The student asked:
        {question}

        This topic isn't directly covered in our COMP237 course materials.

        YOUR TASK:
        - Acknowledge it's outside the course scope
        - Instead of explaining it fully, ask 1-2 guiding questions that help them think about it
        - Optionally connect it to a COMP237 concept if relevant
        - Stay encouraging and brief (3-4 sentences max)

        Example format:
        "This goes beyond our COMP237 materials, but great question! What do you think [guiding question]? How might this relate to [COMP237 concept we studied]?"
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
    conversation_history = state.get("conversation_history", [])

    # ----------------------------------------------------------------------
    # Format conversation history for context
    # ----------------------------------------------------------------------
    history_text = ""
    previous_topic = None
    if conversation_history and len(conversation_history) > 0:
        history_lines = []
        # Get the last 6 messages for display
        for msg in conversation_history[-6:]:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if role == "student":
                history_lines.append(f"Student: {content}")
            elif role == "assistant":
                history_lines.append(f"AI Tutor: {content}")
        
        # Extract the ACTUAL topic from the most recent student question
        # Look backwards through history for the last substantive student question
        for msg in reversed(conversation_history):
            if msg.get("role") == "student":
                student_msg = msg.get("content", "").lower().strip()
                
                # Skip follow-up responses that indicate confusion/stuck
                stuck_phrases = [
                    "didn't understand", "didnt understand", "don't understand", "dont understand",
                    "don't know", "dont know", "idk", "i dont know", "i don't know",
                    "make sense", "didn't make", "didnt make"
                ]
                
                # Check if it's a standalone short response
                is_short_followup = len(student_msg) < 10 and student_msg in ["no", "yes", "ok", "nope", "yeah", "yep"]
                
                # Check if it contains stuck phrases
                is_stuck_phrase = any(phrase in student_msg for phrase in stuck_phrases)
                
                print(f"[TutorAgent] Checking message: '{student_msg[:50]}' | stuck={is_stuck_phrase} | short={is_short_followup}")
                
                # If it's NOT a stuck phrase or short followup, AND has some content, use it
                if not is_stuck_phrase and not is_short_followup and len(student_msg) > 5:
                    previous_topic = msg.get("content", "")
                    print(f"[TutorAgent] ✓ Found previous substantive question: {previous_topic}")
                    break
        
        history_text = "\n".join(history_lines)
        print(f"[TutorAgent] Using conversation history ({len(conversation_history)} messages)")
    
    # If topic is generic like "continue previous explanation", use the actual previous topic
    generic_topic_phrases = [
        "continue", "previous", "follow up", "clarification", 
        "didn't understand", "didnt understand", "confusion",
        "not clear", "unclear"
    ]
    if topic and any(x in topic.lower() for x in generic_topic_phrases):
        if previous_topic:
            topic = previous_topic
            print(f"[TutorAgent] Replaced generic topic '{plan.get('topic')}' with actual previous topic: {topic}")
        else:
            print(f"[TutorAgent] WARNING: Generic topic '{topic}' but no previous_topic found!")

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

    # ----------------------------------------------------------------------
    # NEW: Detect "STUCK" patterns - student needs direct explanation
    # ----------------------------------------------------------------------
    stuck_patterns = [
        "i don't understand", "i dont understand", "dont understand", "don't understand",
        "explain it", "explain to me", "explain this", "tell me",
        "just tell me", "give me the answer", "what is the answer",
        "i'm confused", "im confused", "still confused", "confused",
        "i don't know", "i dont know", "idk", "dont know",
        "didn't make sense", "didnt make sense", "doesn't make sense",
        "can you explain", "please explain", "explain again",
        "i need help", "help me understand", "not clear", "unclear"
    ]
    
    is_stuck = any(pattern in q_lower for pattern in stuck_patterns)
    
    # Count stuck indicators in conversation history
    stuck_count = 0
    if conversation_history:
        for msg in conversation_history:
            if msg.get("role") == "student":
                msg_lower = msg.get("content", "").lower()
                if any(pattern in msg_lower for pattern in stuck_patterns):
                    stuck_count += 1
    
    # Determine escalation level
    escalation_level = 1  # Default: hints first
    if is_stuck:
        if stuck_count >= 2:
            escalation_level = 4  # Full explanation mode
            print(f"[TutorAgent] 🚨 STUCK DETECTED (count={stuck_count}) → Escalation Level 4 (full explanation)")
        elif stuck_count == 1:
            escalation_level = 3  # Concrete example mode
            print(f"[TutorAgent] ⚠️ STUCK DETECTED (count={stuck_count}) → Escalation Level 3 (concrete example)")
        else:
            escalation_level = 2  # More specific hint
            print(f"[TutorAgent] ⚠️ STUCK DETECTED (first time) → Escalation Level 2 (specific hint)")
    else:
        # NOT stuck - this is either a new question or a follow-up attempt
        # Always start with hints (Level 1) for new questions on a topic
        escalation_level = 1
        print(f"[TutorAgent] New/follow-up question (not stuck) → Escalation Level 1 (hints first)")

    print(f"[TutorAgent] Processing Topic: {topic} | mode={mode} | escalation_level={escalation_level} | stuck_count={stuck_count}")

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

        # Pass escalation_level to the prompt for proper response behavior
        messages = TUTOR_IN_SCOPE_PROMPT.format_messages(
            mode=mode,
            escalation_level=escalation_level,
            history=history_text if history_text else "No previous conversation.",
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
