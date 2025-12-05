# Source Metadata Fix: Eliminating "Unknown" Sources

## The Problem

Users see `[Sources: Unknown, Unknown]` instead of proper citations like `[Sources: COMP_237_COURSEOUTLINE.pdf, module3_slides.pdf]`.

This undermines trust and defeats the purpose of RAG-based teaching.

---

## Root Cause Analysis

The source metadata is lost at **multiple points** in the pipeline:

### Point 1: ChromaDB Storage ✅ (Working)

```python
# langchain_chroma.py - metadata is stored correctly
metadata = {
    "source_file": filename,
    "source_filename": filename,
    "course_id": "COMP237",
    "chunk_index": i,
    ...
}
```

### Point 2: Retrieval ✅ (Working)

```python
# RAGAgent.retrieve_context() returns:
[
    {
        "content": "...",
        "source_filename": "COMP_237_COURSEOUTLINE.pdf",  # ✅ Present
        "relevance_score": 0.65
    }
]
```

### Point 3: Tool Output Processing ❌ (BROKEN)

In `tutor_agent.py`, the tool output processing doesn't preserve source metadata:

```python
# tutor_agent.py - Line ~320
async for event in agent.astream_events({"messages": messages}, version="v2"):
    if event["event"] == "on_tool_end":
        tool_output = event["data"].get("output", {})
        # Tool output has sources, but we don't extract them here!
```

### Point 4: Response Source Assembly ❌ (BROKEN)

```python
# sub_agents.py - generate_response_node()
source = doc.get("source_filename") or doc.get("metadata", {}).get("source_filename", "Unknown")
#                                     ^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^
# This fallback chain is fragile - depends on exact key names
```

### Point 5: State → Frontend Transfer ❌ (BROKEN)

```python
# tutor_agent.py - _process_event()
def _process_event(event, state):
    # Sources are pulled from state, but format varies
    sources = state.get("response_sources", [])
    # Sometimes it's a list of strings, sometimes a list of dicts
    # The frontend expects a specific format
```

---

## The Fix: Unified Source Metadata Pipeline

### Step 1: Standardize Source Format

Create a consistent `Source` dataclass:

```python
# NEW: backend/app/agents/source_metadata.py

from dataclasses import dataclass
from typing import Optional, List, Dict, Any

@dataclass
class Source:
    """Standardized source metadata."""
    filename: str
    chunk_index: int
    relevance_score: float
    content_preview: str
    content_type: Optional[str] = None
    page_number: Optional[int] = None
    url: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "title": self.filename,
            "url": self.url or "",
            "description": f"Chunk {self.chunk_index} • Score {self.relevance_score:.2f} • {self.content_preview[:100]}...",
            "filename": self.filename,
            "chunk_index": self.chunk_index,
            "relevance_score": self.relevance_score,
            "content_type": self.content_type,
            "page_number": self.page_number
        }
    
    def to_citation(self) -> str:
        """Format for inline citation."""
        if self.page_number:
            return f"[{self.filename}, p.{self.page_number}]"
        return f"[{self.filename}]"
    
    @classmethod
    def from_rag_result(cls, result: Dict[str, Any]) -> "Source":
        """Create Source from RAG retrieval result."""
        # Handle various key naming conventions
        filename = (
            result.get("source_filename") or
            result.get("source_file") or
            result.get("metadata", {}).get("source_filename") or
            result.get("metadata", {}).get("source_file") or
            result.get("metadata", {}).get("source") or
            "Unknown"
        )
        
        chunk_index = (
            result.get("chunk_index") or
            result.get("metadata", {}).get("chunk_index") or
            0
        )
        
        relevance_score = (
            result.get("relevance_score") or
            result.get("score") or
            result.get("distance") or
            0.0
        )
        # If it's a distance, convert to similarity score
        if relevance_score > 1.0:
            relevance_score = 1.0 - min(relevance_score, 2.0) / 2.0
        
        content = (
            result.get("content") or
            result.get("text") or
            result.get("page_content") or
            ""
        )
        
        return cls(
            filename=filename,
            chunk_index=chunk_index,
            relevance_score=relevance_score,
            content_preview=content[:200] if content else "",
            content_type=result.get("content_type") or result.get("metadata", {}).get("content_type"),
            page_number=result.get("page_number") or result.get("metadata", {}).get("page_number"),
            url=result.get("public_url") or result.get("metadata", {}).get("public_url")
        )


def extract_sources(rag_results: List[Dict[str, Any]]) -> List[Source]:
    """Extract and deduplicate sources from RAG results."""
    sources = []
    seen_files = set()
    
    for result in rag_results:
        source = Source.from_rag_result(result)
        
        # Skip duplicates from same file (keep highest relevance)
        if source.filename in seen_files:
            continue
        seen_files.add(source.filename)
        
        # Skip unknown sources only if we have real sources
        if source.filename == "Unknown" and len(sources) > 0:
            continue
        
        sources.append(source)
    
    # Sort by relevance
    sources.sort(key=lambda s: s.relevance_score, reverse=True)
    
    return sources


def format_sources_for_response(sources: List[Source], max_sources: int = 3) -> str:
    """Format sources for appending to response."""
    if not sources or all(s.filename == "Unknown" for s in sources):
        return ""
    
    valid_sources = [s for s in sources if s.filename != "Unknown"][:max_sources]
    
    if not valid_sources:
        return ""
    
    citations = [s.to_citation() for s in valid_sources]
    return f"\n\n**Sources:** {', '.join(citations)}"
```

### Step 2: Fix RAGAgent

Update `sub_agents.py`:

```python
# sub_agents.py - Update RAGAgent.retrieve_context()

from app.agents.source_metadata import Source, extract_sources

class RAGAgent:
    def retrieve_context(self, query: str, course_id: str = "COMP237") -> List[Dict]:
        """Retrieve relevant context from ChromaDB using LangChain."""
        try:
            records = self.vectorstore.retrieve_with_metadata(
                query=query,
                k=5,
                filter={"course_id": course_id}
            )
            
            # Ensure consistent metadata structure
            normalized = []
            for record in records:
                # Create Source to normalize, then convert back
                source = Source.from_rag_result(record)
                normalized.append({
                    "content": record.get("content") or record.get("text", ""),
                    "source_filename": source.filename,  # Guaranteed to exist
                    "chunk_index": source.chunk_index,
                    "relevance_score": source.relevance_score,
                    "content_type": source.content_type,
                    "page_number": source.page_number,
                    "url": source.url,
                    # Keep original metadata for debugging
                    "_original_metadata": record.get("metadata", {})
                })
            
            logger.info(f"✅ Retrieved {len(normalized)} documents, sources: {[r['source_filename'] for r in normalized]}")
            return normalized
            
        except Exception as e:
            logger.error(f"❌ Error retrieving context: {e}")
            return []
```

### Step 3: Fix Tool Output Processing

Update `tutor_agent.py`:

```python
# tutor_agent.py - Update _process_event()

from app.agents.source_metadata import Source, extract_sources, format_sources_for_response

async def astream_agent(query, user_id, user_email, session_id, chat_id, conversation_history):
    # ... existing setup ...
    
    collected_sources: List[Source] = []  # Collect sources throughout processing
    
    async for event in graph.astream_events(initial_state, version="v2"):
        event_type = event.get("event")
        
        if event_type == "on_tool_end":
            tool_name = event.get("name")
            tool_output = event["data"].get("output", {})
            
            # Extract sources from tool output
            if tool_name == "retrieve_context" and isinstance(tool_output, list):
                new_sources = extract_sources(tool_output)
                collected_sources.extend(new_sources)
                logger.info(f"📚 Collected {len(new_sources)} sources: {[s.filename for s in new_sources]}")
        
        elif event_type == "on_chat_model_stream":
            # ... existing streaming logic ...
            pass
    
    # After streaming complete, format sources
    if collected_sources:
        sources_text = format_sources_for_response(collected_sources)
        if sources_text:
            yield {
                "type": "text-delta",
                "textDelta": sources_text
            }
        
        # Also send structured source data for frontend
        yield {
            "type": "sources",
            "sources": [s.to_dict() for s in collected_sources[:5]]
        }
```

### Step 4: Fix generate_response_node

```python
# sub_agents.py - Fix generate_response_node()

from app.agents.source_metadata import Source, extract_sources, format_sources_for_response

def generate_response_node(state: AgentState) -> AgentState:
    # ... existing setup ...
    
    retrieved_context = state.get("retrieved_context", [])
    
    # Use standardized source extraction
    sources = extract_sources(retrieved_context)
    
    # Build context string
    context_parts = []
    for doc in retrieved_context[:3]:
        content = doc.get("content") or doc.get("text", "")
        context_parts.append(content)
    
    context_str = "\n\n---\n\n".join(context_parts)
    
    # ... generate response ...
    
    # Add sources to response
    if sources:
        sources_text = format_sources_for_response(sources)
        response_text += sources_text
    
    state["response"] = response_text
    
    # Store structured source data
    state["response_sources"] = [s.to_dict() for s in sources]
    
    return state
```

---

## Verification Steps

### Test 1: RAG Retrieval Sources

```python
# test_source_metadata.py

def test_rag_returns_sources():
    """Verify RAG retrieval includes source metadata."""
    from app.agents.sub_agents import RAGAgent
    
    agent = RAGAgent()
    results = agent.retrieve_context("gradient descent")
    
    assert len(results) > 0, "Should retrieve documents"
    
    for result in results:
        assert "source_filename" in result, "Should have source_filename"
        assert result["source_filename"] != "Unknown", f"Should not be Unknown, got: {result}"

def test_source_extraction():
    """Verify Source class handles various formats."""
    from app.agents.source_metadata import Source
    
    # Test with nested metadata
    result1 = {
        "content": "Test content",
        "metadata": {
            "source_file": "test.pdf",
            "chunk_index": 3
        }
    }
    source1 = Source.from_rag_result(result1)
    assert source1.filename == "test.pdf"
    
    # Test with flat structure
    result2 = {
        "content": "Test content",
        "source_filename": "test2.pdf",
        "chunk_index": 5
    }
    source2 = Source.from_rag_result(result2)
    assert source2.filename == "test2.pdf"
```

### Test 2: End-to-End Source Display

```python
def test_agent_returns_sources():
    """Verify agent response includes proper sources."""
    from app.agents.tutor_agent import run_agent
    
    result = run_agent("explain gradient descent", "test-user", "test@test.com")
    
    sources = result.get("sources", [])
    assert len(sources) > 0, "Should have sources"
    
    for source in sources:
        assert source.get("filename") != "Unknown", f"Source should not be Unknown: {source}"
```

---

## Frontend Updates Needed

The frontend should handle the new `sources` event type:

```typescript
// extension/src/hooks/use-chat.ts

// Handle sources event
if (event.type === "sources") {
  setSources(event.sources.map(s => ({
    title: s.filename,
    url: s.url,
    description: s.description
  })));
}
```

---

## Summary of Changes

| File | Change |
|------|--------|
| `backend/app/agents/source_metadata.py` | NEW - Source dataclass and utilities |
| `backend/app/agents/sub_agents.py` | Fix RAGAgent and generate_response_node |
| `backend/app/agents/tutor_agent.py` | Add source collection during streaming |
| `backend/tests/test_source_metadata.py` | NEW - Source handling tests |

---

## Expected Outcome

**Before:**
```
[Sources: Unknown, Unknown]
```

**After:**
```
**Sources:** [COMP_237_COURSEOUTLINE.pdf], [module3_optimization.pdf, p.12]
```
