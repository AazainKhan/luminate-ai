"""
Context Agent for Navigate Mode
Adds related topics, prerequisites, and next steps using graph relationships.
"""

from typing import Dict, List, Set
import json
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables (if needed for future LLM integration)
load_dotenv()

import json
from typing import Dict, Any, List
from pathlib import Path


# Path to graph data
GRAPH_DATA_PATH = Path(__file__).parent.parent.parent.parent.parent / "comp_237_content" / "graph_data.json"


def context_agent(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich retrieved results with graph-based context.
    
    Args:
        state: LangGraph state containing 'retrieved_chunks'
        
    Returns:
        Updated state with 'enriched_results' containing context-enhanced results
    """
    retrieved_chunks = state.get("retrieved_chunks", [])
    
    if not retrieved_chunks:
        state["enriched_results"] = []
        return state
    
    # Load graph data
    graph_data = _load_graph_data()
    
    if not graph_data:
        # No graph available, pass through
        state["enriched_results"] = retrieved_chunks
        state["context_warning"] = "Graph data not available"
        return state
    
    # Build lookup maps for efficient graph traversal
    doc_id_to_node = {node["id"]: node for node in graph_data.get("nodes", [])}
    relationships = graph_data.get("relationships", [])
    
    # Enrich top 10 results (limit to avoid too much processing)
    enriched = []
    for chunk in retrieved_chunks[:10]:
        bb_doc_id = chunk.get("metadata", {}).get("bb_doc_id")
        
        if bb_doc_id and bb_doc_id in doc_id_to_node:
            # Add graph context
            context = _get_document_context(bb_doc_id, doc_id_to_node, relationships)
            chunk["graph_context"] = context
        else:
            chunk["graph_context"] = None
        
        enriched.append(chunk)
    
    # Pass through remaining results without graph context
    enriched.extend(retrieved_chunks[10:])
    
    state["enriched_results"] = enriched
    
    return state


def _load_graph_data() -> Dict:
    """Load graph data from JSON file."""
    try:
        if not GRAPH_DATA_PATH.exists():
            print(f"Graph data not found at: {GRAPH_DATA_PATH}")
            return {}
        
        with open(GRAPH_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading graph data: {e}")
        return {}


def _get_document_context(
    doc_id: str,
    doc_id_to_node: Dict,
    relationships: List[Dict]
) -> Dict[str, Any]:
    """
    Get context for a document from the graph.
    
    Args:
        doc_id: Blackboard document ID
        doc_id_to_node: Map of doc_id to node data
        relationships: List of all relationships
        
    Returns:
        Dictionary with related_topics, prerequisites, next_steps, module_info
    """
    context = {
        "module": None,
        "related_topics": [],
        "prerequisites": [],
        "next_steps": []
    }
    
    # Get node info
    node = doc_id_to_node.get(doc_id, {})
    
    # Module info
    context["module"] = node.get("module")
    
    # Find relationships
    for rel in relationships:
        source = rel.get("source")
        target = rel.get("target")
        rel_type = rel.get("type")
        
        # Related topics (documents in same module via CONTAINS)
        if rel_type == "CONTAINS" and target == doc_id:
            # Source is the module/parent
            parent_node = doc_id_to_node.get(source, {})
            if parent_node.get("type") == "module":
                context["module"] = parent_node.get("title")
        
        # Sequential relationships
        if source == doc_id:
            if rel_type == "NEXT_IN_MODULE":
                # This document comes before target
                next_node = doc_id_to_node.get(target, {})
                if next_node:
                    context["next_steps"].append({
                        "id": target,
                        "title": next_node.get("title", "Unknown"),
                        "type": next_node.get("type", "document")
                    })
            
        if target == doc_id:
            if rel_type == "PREV_IN_MODULE":
                # Source comes before this document
                prev_node = doc_id_to_node.get(source, {})
                if prev_node:
                    context["prerequisites"].append({
                        "id": source,
                        "title": prev_node.get("title", "Unknown"),
                        "type": prev_node.get("type", "document")
                    })
    
    # Find sibling documents (other docs in same module) for related topics
    if context["module"]:
        for rel in relationships:
            if rel.get("type") == "CONTAINS":
                # Find all docs in same module
                sibling_id = rel.get("target")
                if sibling_id != doc_id and sibling_id in doc_id_to_node:
                    sibling = doc_id_to_node[sibling_id]
                    if sibling.get("module") == context["module"]:
                        context["related_topics"].append({
                            "id": sibling_id,
                            "title": sibling.get("title", "Unknown"),
                            "type": sibling.get("type", "document")
                        })
    
    # Limit lists
    context["related_topics"] = context["related_topics"][:3]
    context["prerequisites"] = context["prerequisites"][:2]
    context["next_steps"] = context["next_steps"][:2]
    
    return context


if __name__ == "__main__":
    # Test the agent
    print("Testing Context Agent\n")
    
    # Mock retrieved chunks
    test_state = {
        "retrieved_chunks": [
            {
                "content": "Neural networks are...",
                "metadata": {
                    "bb_doc_id": "_123456_1",
                    "title": "Introduction to Neural Networks",
                    "module": "Module 3: Machine Learning"
                },
                "score": 0.89
            },
            {
                "content": "Backpropagation algorithm...",
                "metadata": {
                    "bb_doc_id": "_123457_1",
                    "title": "Backpropagation",
                    "module": "Module 3: Machine Learning"
                },
                "score": 0.85
            }
        ]
    }
    
    result = context_agent(test_state)
    
    enriched = result["enriched_results"]
    
    print(f"Enriched {len(enriched)} results\n")
    
    for i, chunk in enumerate(enriched, 1):
        print(f"\n{i}. {chunk.get('metadata', {}).get('title', 'N/A')}")
        
        graph_context = chunk.get("graph_context")
        if graph_context:
            print(f"   Module: {graph_context.get('module', 'N/A')}")
            print(f"   Related Topics: {len(graph_context.get('related_topics', []))}")
            print(f"   Prerequisites: {len(graph_context.get('prerequisites', []))}")
            print(f"   Next Steps: {len(graph_context.get('next_steps', []))}")
            
            if graph_context.get("prerequisites"):
                print(f"   → Prerequisites:")
                for prereq in graph_context["prerequisites"]:
                    print(f"      - {prereq['title']}")
        else:
            print(f"   No graph context available")
