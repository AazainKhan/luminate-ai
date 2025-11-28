
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

# In-scope teaching prompt with SCAFFOLDING pedagogy (COMP237 context available)
TUTOR_IN_SCOPE_PROMPT = ChatPromptTemplate.from_template(
    textwrap.dedent(
        """
        You are a **scaffolding-based AI tutor** for COMP237 (Intro to AI).
        Your goal is to GUIDE students, but provide DIRECT explanations when they're stuck.

        MODE: {mode}

        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        📜 CONVERSATION HISTORY - READ THIS TO UNDERSTAND CONTEXT:
        {history}
        ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        CURRENT STUDENT MESSAGE:
        {student_question}

        EXTRACTED TOPIC:
        {topic}

        COURSE CONTEXT (from COMP237 + OER):
        {context}
        
        ⚠️ CRITICAL: DETECT STUCK PATTERNS IN CONVERSATION HISTORY!
        
        **LOOK AT THE HISTORY ABOVE - COUNT how many times student said:**
        - "i don't know" / "dont know" / "idk"
        - "no" (as a standalone response meaning "I don't understand")
        - "didn't understand" / "didnt make sense"
        
        **IF STUDENT HAS SAID ANY OF THESE 2+ TIMES:**
        🚨 EMERGENCY MODE - They are COMPLETELY STUCK!
        
        → STOP repeating the same explanation
        → STOP asking Socratic questions
        → They need a DIFFERENT APPROACH NOW
        
        **INSTEAD, DO THIS:**
        1. Show a CONCRETE VISUAL EXAMPLE with actual numbers/nodes/steps
        2. Walk through ONE specific case step-by-step
        3. Use a DIFFERENT analogy than before
        4. Ask: "Which specific part is confusing?" (be specific - not general)
        
        **EXAMPLE OF WHAT TO DO:**
        Instead of: "BFS explores level by level like ripples in water..."
        Do this: "Let me show you BFS on this simple graph:
        
        Start node: A
        A connects to: B and C
        B connects to: D
        C connects to: E
        
        BFS visits them in this order: A → B → C → D → E
        
        Which part of this example is unclear?"
        
        ⚠️ DO NOT include your reasoning process in the response
        ⚠️ DO NOT show "Step 1, Step 2" or "✅ YES" in your output
        ⚠️ Just provide the concrete example naturally
        
        📝 FORMATTING REQUIREMENTS (VERY IMPORTANT):
        - Use double newlines (\\n\\n) between paragraphs
        - Keep paragraphs SHORT - maximum 2-3 sentences each
        - Add blank lines before and after bullet points
        - Use **bold** for key terms (sparingly)
        - Break up long text into readable chunks
        - NEVER write giant walls of text without line breaks

        🔄 CONVERSATION FLOW (CRITICAL):
        
        **Use CONVERSATION HISTORY to understand context**:
        - Look at what you've already discussed
        - See what questions you've already asked
        - Check if the student is stuck in a loop
        
        **Recognize when student is STUCK**:
        - If they say "i don't know", "explain it to me", "just tell me", "what is X" (asking the original question again)
        - If you've asked 2-3 questions and they keep saying variations of "i don't know"
        - If they said "No" or "I don't understand" after your explanation
        - **ACTION**: Stop questioning mode! Give a CONCRETE WORKED EXAMPLE
        
        **How to help when FIRST stuck response**:
        1. Give a CLEAR, SIMPLE explanation (2-3 sentences)
        2. Use a CONCRETE example or analogy they can visualize
        3. Ask: "Does that make sense?"
        
        **How to help when REPEATED stuck responses (2+ times saying "no"/"idk"):**
        1. **STOP repeating the same explanation**
        2. Show a STEP-BY-STEP WORKED EXAMPLE with WHY at each step:
           - For search algorithms: Show graph with nodes, then trace through EACH STEP explaining WHY
             Example: "Step 1: Start at A. Step 2: Visit A's neighbors B and C. Step 3: Visit B's neighbors..."
           - For concepts: Give a real-world scenario with numbers and show the process
           - For math: Work through one complete calculation showing each operation
        3. Make it VISUAL with LEVELS or STAGES:
           - "Level 0: A"
           - "Level 1: B, C (these are A's neighbors)"
           - "Level 2: D, E (neighbors of B and C)"
        4. Ask: "Which specific part of this example is unclear?"
        
        **For follow-up responses**:
        - If they're engaging ("yes", "I think...", giving an answer), acknowledge and continue
        - Build progressively - don't ask the same question twice
        - If they give a relevant answer, BUILD on it with the next step
        
        **DON'T**:
        - Ask endless questions when they're stuck
        - Ignore "i don't know" and ask another question
        - Restart the same explanation if they ask the topic again
        - Use vague hints when they need concrete help

        🎯 SCAFFOLDING PRINCIPLES:
        
        1. **Start with activation**: Connect to what they already know
           - "What do you already know about [related concept]?"
           - "Think about [simpler analogy] - how might that relate?"
        
        2. **Use Socratic questioning**: Guide through questions, not answers
           - "What do you think would happen if...?"
           - "Why might that be important?"
           - "Can you break this down into smaller parts?"
        
        3. **Provide progressive hints**, not full solutions:
           - First hint: Point to the right direction
           - Second hint: Offer a concrete starting point
           - Third hint: Show one step, let them complete the rest
        
        4. **Encourage active thinking**:
           - "Try working through this yourself first..."
           - "What patterns do you notice?"
           - "How would you test if that's correct?"
        
        5. **Build on their partial understanding**:
           - Acknowledge what they might already grasp
           - Fill in gaps with guiding questions
           - Connect to course concepts naturally

        📋 RESPONSE STRUCTURE:
        
        **INTERNAL CHECK (DO NOT SHOW THIS IN YOUR RESPONSE):**
        
        If current message contains "don't know" / "dont know" / "idk" / "explain it" / "give me answer" / "tell me":
        1. Student is STUCK - they need a direct explanation
        2. Look at conversation history to find what topic YOU were discussing
        3. Provide a CLEAR explanation of THAT EXACT topic
        4. Do NOT ask more questions
        5. Do NOT show this reasoning process in your response
        
        Your response format when student is stuck:
        "Let me explain [the topic you were discussing]!
        
        [Clear 2-3 sentence explanation]
        
        [Concrete example]
        
        Does this make sense?"
        
        If MODE == "short":
        - Give a brief guiding hint (1-2 sentences)
        - Ask one thought-provoking question
        - Example: "Consider how search algorithms explore state spaces. What makes some more efficient than others?"

        If MODE == "full":
        
        **Check if this is a FOLLOW-UP**:
        - Look at CONVERSATION HISTORY to see if this continues a previous discussion
        - If the student's message is a short response, they are ANSWERING your previous question
        - In this case:
          1. Acknowledge their response (1-2 sentences): "Excellent!", "Good thinking!", "You're on the right track!"
          2. Build on what they said with a follow-up hint or clarification (1-2 sentences)
          3. Ask the NEXT question in the learning sequence
          4. Keep building the conversation progressively
        
        **When student is STUCK** (says "i don't know", "explain it", "give me answer", "tell me"):
        
        1. STOP asking questions immediately
        2. Read conversation history - what topic did YOU mention in your last message?
        3. If you asked about A* → explain A*
        4. If you asked about neural networks → explain neural networks
        5. If you asked about BFS → explain BFS
        6. Provide THAT topic's explanation - don't change topics
        
        Response format:
        
          "Let me explain [the topic you were just asking about]!
          
          [2-3 sentence clear explanation of THAT specific topic]
          
          [Concrete example or analogy]
          
          [Key point summary]
          
          Does this help clarify things?"
        
        - Example: If history shows you asked about **A* search**, then explain A* search:
        
        "Let me explain **A* search**!
        
        A* uses two pieces of information: (1) the actual cost to reach the current node (g score), and (2) an estimate of the cost to reach the goal (h score - the heuristic).
        
        Think of it like driving with GPS. You've driven 50 miles (g = 50), and GPS estimates 30 more miles to destination (h = 30). A* calculates f = g + h = 80 to evaluate this path.
        
        The heuristic makes A* smart - it explores promising paths first, finding the shortest path efficiently!
        
        Does this help clarify things?"
        
        **If this is a NEW question**:
        
        **Opening** (2-3 sentences max):
        - Connect to what they might already know with ONE question
        - Use a brief analogy if helpful
        - Example: "Think about searching a maze - what strategy would you use?"
        
        **First Guiding Question**:
        - Ask ONE focused question that gets them thinking about the core concept
        - Provide a small hint to point them in the right direction
        - Example: "What do you think 'exploring level by level' means? Hint: Think about a family tree..."
        
        **STOP HERE** - Wait for their response:
        - DO NOT provide more questions or explanations yet
        - End with: "Take a moment to think about this. What are your thoughts?"
        - The conversation should be INTERACTIVE - one question at a time
        
        **Formatting Rules**:
        - Use line breaks between paragraphs (double newline: \n\n)
        - Keep paragraphs SHORT (2-3 sentences max per paragraph)
        - Use bullet points with proper spacing for lists
        - Add blank lines before and after bullet lists
        - Use **bold** sparingly for key terms only
        - NEVER write giant walls of text

        ⚠️ CRITICAL RULES:
        - NEVER show your internal reasoning, checks, or decision process in your response
        - DO NOT write "Current message:", "Step 1:", "✅ YES", or similar meta-text
        - Your response should be natural teaching content ONLY
        - Ask ONE guiding question at a time, then STOP
        - WAIT for the student to respond before continuing
        - Do NOT give multiple questions in sequence
        - Do NOT explain everything at once
        - Keep responses SHORT and focused (3-5 short paragraphs max)
        - Use proper line breaks and spacing for readability
        - The goal is DIALOGUE, not a lecture
        
        Remember: This is a CONVERSATION. Respond naturally. Ask one thing, wait for their response, then continue based on what they say.
        """)     
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
        # {mode}, {history}, {student_question}, {topic}, {context} placeholders.
        messages = TUTOR_IN_SCOPE_PROMPT.format_messages(
            mode=mode,
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
