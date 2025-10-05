"""
Retrieval Agent for Navigate Mode
Retrieves documents directly from ChromaDB, re-ranks results, removes duplicates.
"""

from typing import Dict, List, Any
import json
from llm_config import get_llm


def retrieval_agent(state: Dict) -> Dict:
    """
    Retrieve relevant documents directly from ChromaDB instance.
    
    Args:
        state: Contains 'parsed_query' with search information and 'chroma_db' instance
        
    Returns:
        Updated state with 'retrieved_chunks' containing top results
    """
    parsed_query = state["parsed_query"]
    chroma_db = state.get("chroma_db")
    
    if not chroma_db:
        print("Error: ChromaDB instance not provided in state")
        state["retrieved_chunks"] = []
        state["retrieval_error"] = "ChromaDB not available"
        return state
    
    # Use expanded query for better retrieval
    search_query = parsed_query.get("expanded_query", state["query"])
    
    try:
        # Query ChromaDB directly
        raw_results = chroma_db.query(query_text=search_query, n_results=15)
        
        # Convert ChromaDB format to expected format
        results = _convert_chromadb_results(raw_results)
        
        if not results:
            state["retrieved_chunks"] = []
            return state
        
        # Re-rank and deduplicate
        reranked = _rerank_results(results)
        deduplicated = _remove_duplicates(reranked)
        
        # Limit to top 10
        state["retrieved_chunks"] = deduplicated[:10]
        
    except Exception as e:
        print(f"Error retrieving from ChromaDB: {e}")
        state["retrieved_chunks"] = []
        state["retrieval_error"] = str(e)
    
    return state


def _convert_chromadb_results(chroma_results: Dict) -> List[Dict]:
    """
    Convert ChromaDB query results to expected format.
    
    Args:
        chroma_results: Raw results from ChromaDB query
        
    Returns:
        List of formatted result dicts
    """
    results = []
    
    if not chroma_results.get("documents") or not chroma_results["documents"][0]:
        return results
    
    for doc, meta, dist in zip(
        chroma_results["documents"][0],
        chroma_results["metadatas"][0],
        chroma_results["distances"][0]
    ):
        # Extract tags
        tags_str = meta.get("tags", "")
        tags = tags_str.split(",") if tags_str else []
        
        result = {
            "content": doc,
            "metadata": {
                "title": meta.get("title", "Untitled"),
                "bb_doc_id": meta.get("bb_doc_id"),
                "live_lms_url": meta.get("live_lms_url"),
                "module": meta.get("module", "Unknown"),
                "content_type": meta.get("content_type", "unknown"),
                "chunk_index": meta.get("chunk_index", 0),
                "total_chunks": meta.get("total_chunks", 1),
                "tags": tags
            },
            "score": float(dist)  # ChromaDB distance (lower is better)
        }
        results.append(result)
    
    return results


def _rerank_results(results: List[Dict]) -> List[Dict]:
    """
    Re-rank results by prioritizing Blackboard documents.
    
    Scoring:
    - Has bb_doc_id: +10 points
    - Has live_lms_url: +5 points
    - Similarity score: original score * 10
    
    Args:
        results: List of search results from ChromaDB
        
    Returns:
        Re-ranked list of results
    """
    scored_results = []
    
    for result in results:
        metadata = result.get("metadata", {})
        similarity = result.get("score", 0.0)
        
        # Calculate score
        score = similarity * 10  # Base score from semantic similarity
        
        if metadata.get("bb_doc_id"):
            score += 10
        
        if metadata.get("live_lms_url"):
            score += 5
        
        result["rerank_score"] = score
        scored_results.append(result)
    
    # Sort by rerank score descending
    scored_results.sort(key=lambda x: x["rerank_score"], reverse=True)
    
    return scored_results


def _remove_duplicates(results: List[Dict]) -> List[Dict]:
    """
    Remove duplicate results with the same bb_doc_id.
    Keep the one with higher rerank score.
    
    Args:
        results: List of search results
        
    Returns:
        Deduplicated list
    """
    seen_bb_ids = set()
    unique_results = []
    
    for result in results:
        bb_doc_id = result.get("metadata", {}).get("bb_doc_id")
        
        if bb_doc_id:
            if bb_doc_id not in seen_bb_ids:
                seen_bb_ids.add(bb_doc_id)
                unique_results.append(result)
        else:
            # Include results without bb_doc_id (shouldn't happen but handle it)
            unique_results.append(result)
    
    return unique_results


if __name__ == "__main__":
    # Test the agent
    print("Testing Retrieval Agent\n")
    print("Note: Requires FastAPI service running at http://localhost:8000\n")
    
    test_state = {
        "query": "neural networks",
        "parsed_query": {
            "expanded_query": "neural networks machine learning",
            "category": "machine learning",
            "search_terms": ["neural", "networks", "deep", "learning", "backpropagation"],
            "student_goal": "learn_concept"
        }
    }
    
    result = retrieval_agent(test_state)
    
    if "retrieval_error" in result:
        print(f"Error: {result['retrieval_error']}")
    else:
        chunks = result["retrieved_chunks"]
        metadata = result["retrieval_metadata"]
        
        print(f"Retrieval Metadata:")
        print(f"  Total results: {metadata['total_results']}")
        print(f"  After rerank: {metadata['after_rerank']}")
        print(f"  After dedup: {metadata['after_dedup']}")
        print(f"  Final count: {metadata['final_count']}")
        print(f"  Search query: {metadata['search_query_used']}")
        print(f"\nTop 3 Results:")
        
        for i, chunk in enumerate(chunks[:3], 1):
            print(f"\n{i}. Title: {chunk.get('metadata', {}).get('title', 'N/A')}")
            print(f"   Score: {chunk.get('score', 0):.4f} | Rerank: {chunk.get('rerank_score', 0):.2f}")
            print(f"   BB ID: {chunk.get('metadata', {}).get('bb_doc_id', 'N/A')}")
            print(f"   Module: {chunk.get('metadata', {}).get('module', 'N/A')}")
