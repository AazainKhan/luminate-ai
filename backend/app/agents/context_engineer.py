"""
Context Engineering Module

Implements context compaction and structured note-taking for long conversations.
Based on Anthropic's context engineering research.

Key features:
- Context compaction: Summarize conversation history when it gets too long
- Structured note-taking: Maintain key concepts and decisions outside context window
- Context window management: Track and optimize token usage
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass
import logging
import json
import time

from app.agents.state import AgentState
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI
from app.config import settings

logger = logging.getLogger(__name__)


@dataclass
class ConversationSummary:
    """Summary of a conversation segment"""
    key_topics: List[str]
    key_concepts: List[str]
    student_questions: List[str]
    tutor_responses: List[str]
    unresolved_questions: List[str]
    timestamp: float


class ContextEngineer:
    """
    Manages context window through compaction and note-taking.
    
    Implements:
    1. Compaction: Summarize old conversation history
    2. Structured note-taking: Track key concepts and decisions
    3. Context window tracking: Monitor token usage
    """
    
    COMPACTION_THRESHOLD = 10  # Compact after 10 turns
    MAX_CONTEXT_LENGTH = 8000  # Max tokens for context (conservative)
    
    def __init__(self):
        """Initialize context engineer"""
        self.compaction_model = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash-exp",  # Using exp version - stable version deprecated
            google_api_key=settings.google_api_key,
            temperature=0.1,
            max_output_tokens=1024,
        )
    
    def should_compact(self, conversation_history: List[dict]) -> bool:
        """Determine if conversation should be compacted"""
        return len(conversation_history) >= self.COMPACTION_THRESHOLD
    
    def compact_conversation(
        self,
        conversation_history: List[dict],
        current_topic: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compact conversation history into a summary.
        
        Preserves:
        - Key topics discussed
        - Key concepts explained
        - Student's learning progress
        - Unresolved questions
        
        Discards:
        - Redundant explanations
        - Tool call details
        - Verbose examples (keeps summaries)
        """
        if not conversation_history:
            return {
                "summary": "No prior conversation.",
                "key_topics": [],
                "key_concepts": [],
                "compacted": False
            }
        
        # Take messages to compact (all but last 4 exchanges)
        messages_to_compact = conversation_history[:-8] if len(conversation_history) > 8 else []
        recent_messages = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
        
        if not messages_to_compact:
            return {
                "summary": "Conversation is still short, no compaction needed.",
                "key_topics": [],
                "key_concepts": [],
                "compacted": False
            }
        
        # Build compaction prompt
        conversation_text = "\n".join([
            f"{msg.get('role', 'unknown').upper()}: {msg.get('content', '')[:500]}"
            for msg in messages_to_compact
        ])
        
        compaction_prompt = f"""Summarize this conversation segment, preserving critical information while removing redundancy.

## Conversation to Compact:
{conversation_text[:4000]}  # Limit input size

## Instructions:
1. Extract key topics and concepts discussed
2. Note student's questions and learning progress
3. Identify any unresolved questions
4. Remove redundant explanations and tool call details
5. Keep the summary concise but informative

## Output Format (JSON):
{{
    "key_topics": ["topic1", "topic2"],
    "key_concepts": ["concept1", "concept2"],
    "student_questions": ["question1", "question2"],
    "tutor_responses_summary": "Brief summary of tutor's explanations",
    "unresolved_questions": ["question1", "question2"],
    "summary": "Overall summary of the conversation segment"
}}"""

        try:
            response = self.compaction_model.invoke([
                SystemMessage(content="You are a conversation summarizer. Extract key information while removing redundancy."),
                HumanMessage(content=compaction_prompt)
            ])
            
            # Handle Gemini 2.5+ list content format
            raw_content = response.content
            if isinstance(raw_content, list):
                text_parts = []
                for block in raw_content:
                    if isinstance(block, dict) and block.get('type') == 'text':
                        text_parts.append(block.get('text', ''))
                    elif isinstance(block, str):
                        text_parts.append(block)
                content = ''.join(text_parts).strip()
            else:
                content = raw_content.strip() if isinstance(raw_content, str) else str(raw_content).strip()
            
            # Parse JSON
            if "```" in content:
                parts = content.split("```")
                if len(parts) >= 2:
                    json_part = parts[1]
                    if json_part.startswith("json"):
                        json_part = json_part[4:]
                    content = json_part.strip()
            
            summary_data = json.loads(content)
            
            logger.info(f"📦 Compacted {len(messages_to_compact)} messages into summary")
            
            return {
                "summary": summary_data.get("summary", ""),
                "key_topics": summary_data.get("key_topics", []),
                "key_concepts": summary_data.get("key_concepts", []),
                "student_questions": summary_data.get("student_questions", []),
                "tutor_responses_summary": summary_data.get("tutor_responses_summary", ""),
                "unresolved_questions": summary_data.get("unresolved_questions", []),
                "compacted": True,
                "compacted_messages": len(messages_to_compact),
                "remaining_messages": len(recent_messages)
            }
            
        except Exception as e:
            logger.warning(f"Compaction failed: {e}, using simple truncation")
            # Fallback: simple truncation
            return {
                "summary": f"Previous conversation covered {len(messages_to_compact)} messages. Recent context preserved.",
                "key_topics": [],
                "key_concepts": [],
                "compacted": True,
                "compacted_messages": len(messages_to_compact),
                "remaining_messages": len(recent_messages)
            }
    
    def build_compacted_history(
        self,
        conversation_history: List[dict],
        compaction_summary: Dict[str, Any]
    ) -> List[dict]:
        """
        Build compacted conversation history with summary + recent messages.
        
        Returns:
            List of messages with summary prepended
        """
        compacted = []
        
        # Add summary as system message
        if compaction_summary.get("compacted"):
            summary_text = f"""## Previous Conversation Summary:
{compaction_summary.get('summary', '')}

Key Topics: {', '.join(compaction_summary.get('key_topics', []))}
Key Concepts: {', '.join(compaction_summary.get('key_concepts', []))}
"""
            if compaction_summary.get("unresolved_questions"):
                summary_text += f"\nUnresolved Questions: {', '.join(compaction_summary.get('unresolved_questions', []))}"
            
            compacted.append({
                "role": "system",
                "content": summary_text,
                "timestamp": time.time()
            })
        
        # Add recent messages (last 8 messages = 4 exchanges)
        recent_messages = conversation_history[-8:] if len(conversation_history) > 8 else conversation_history
        compacted.extend(recent_messages)
        
        return compacted
    
    def create_structured_notes(
        self,
        state: AgentState,
        concept: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Create structured notes for key concepts and decisions.
        
        These notes persist outside the context window and can be referenced later.
        """
        notes = {
            "timestamp": time.time(),
            "concept": concept,
            "intent": state.get("intent"),
            "scaffolding_level": state.get("scaffolding_level"),
            "bloom_level": state.get("bloom_level"),
            "key_points": [],
            "student_understanding": "unknown",  # Will be updated based on follow-ups
        }
        
        # Extract key points from response if available
        response = state.get("response", "")
        if response:
            # Simple extraction: look for key phrases
            key_phrases = []
            sentences = response.split('.')
            for sentence in sentences[:5]:  # First 5 sentences
                if any(marker in sentence.lower() for marker in ['is a', 'means', 'works by', 'the key']):
                    key_phrases.append(sentence.strip())
            notes["key_points"] = key_phrases[:3]  # Keep top 3
        
        return notes
    
    def engineer_context(
        self,
        state: AgentState
    ) -> AgentState:
        """
        Main context engineering function.
        
        Performs:
        1. Check if compaction is needed
        2. Compact if necessary
        3. Build optimized context
        4. Create structured notes
        
        Returns:
            Updated state with engineered context
        """
        conversation_history = state.get("conversation_history", []) or []
        
        # Check if compaction is needed
        if self.should_compact(conversation_history):
            logger.info(f"📦 Compacting conversation: {len(conversation_history)} messages")
            
            # Get current topic from state
            current_topic = state.get("key_concepts_detected", [])
            if current_topic:
                current_topic = current_topic[0] if isinstance(current_topic, list) else str(current_topic)
            
            # Compact
            compaction_summary = self.compact_conversation(conversation_history, current_topic)
            
            # Build compacted history
            compacted_history = self.build_compacted_history(conversation_history, compaction_summary)
            
            # Update state
            state_updates = {
                "conversation_history": compacted_history,
                "context_compacted": True,
                "compaction_summary": compaction_summary
            }
            
            # Create structured notes for key concepts
            concept = state.get("key_concepts_detected", [])
            if concept:
                concept = concept[0] if isinstance(concept, list) else str(concept)
                notes = self.create_structured_notes(state, concept)
                state_updates["structured_notes"] = notes
            
            logger.info(f"📦 Compaction complete: {len(compacted_history)} messages (from {len(conversation_history)})")
            
            return state_updates
        
        # No compaction needed
        return {}


# Global instance
_context_engineer = ContextEngineer()


def engineer_context(state: AgentState) -> AgentState:
    """
    Convenience function to engineer context.
    
    Args:
        state: Current agent state
        
    Returns:
        Updated state with engineered context
    """
    updates = _context_engineer.engineer_context(state)
    # Merge updates into state (state is TypedDict, so we return updates)
    return updates
