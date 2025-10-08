#!/usr/bin/env python3
"""
Export LangGraph configurations to JSON for LangFlow import.

This script dumps the structure of Navigate and Educate mode graphs
to JSON files that can be imported into LangFlow.

Usage:
    python scripts/export_langgraph.py
"""

import sys
import json
from pathlib import Path
from typing import Dict, List, Any

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "development" / "backend" / "langgraph"))

from navigate_graph import build_navigate_graph
from educate_graph import build_educate_graph


def extract_graph_structure(graph, graph_name: str) -> Dict[str, Any]:
    """
    Extract nodes and edges from a compiled LangGraph.
    
    Args:
        graph: Compiled StateGraph
        graph_name: Name of the graph (navigate/educate)
    
    Returns:
        Dictionary with nodes, edges, and metadata
    """
    # Access the internal graph structure
    # LangGraph stores compiled graph in .graph attribute
    internal_graph = graph.graph if hasattr(graph, 'graph') else graph
    
    nodes = []
    edges = []
    
    # Extract nodes
    if hasattr(internal_graph, 'nodes'):
        for node_id in internal_graph.nodes:
            node_data = {
                "id": node_id,
                "type": "agent" if node_id != "__start__" and node_id != "__end__" else "control",
                "name": node_id.replace('_', ' ').title(),
                "description": f"Agent: {node_id}" if node_id not in ["__start__", "__end__"] else f"Control: {node_id}"
            }
            nodes.append(node_data)
    
    # Extract edges
    if hasattr(internal_graph, 'edges'):
        for edge in internal_graph.edges:
            if isinstance(edge, tuple) and len(edge) >= 2:
                edge_data = {
                    "source": edge[0],
                    "target": edge[1],
                    "type": "sequential"
                }
                edges.append(edge_data)
    
    # Handle conditional edges if present
    if hasattr(internal_graph, '_all_edges'):
        for source, branches in internal_graph._all_edges.items():
            if isinstance(branches, dict):
                for condition, target in branches.items():
                    edge_data = {
                        "source": source,
                        "target": target,
                        "type": "conditional",
                        "condition": str(condition)
                    }
                    edges.append(edge_data)
    
    return {
        "graph_name": graph_name,
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "entry_point": "understand_query",
            "export_version": "1.0"
        }
    }


def export_navigate_graph() -> Dict[str, Any]:
    """Export Navigate Mode graph structure."""
    print("📊 Exporting Navigate Mode graph...")
    
    try:
        graph = build_navigate_graph()
        structure = extract_graph_structure(graph, "navigate_mode")
        
        # Manually add edges based on documented workflow
        # Navigate flow: understand_query → retrieve → search_external → add_context → format_response
        structure["edges"] = [
            {"source": "__start__", "target": "understand_query", "type": "sequential"},
            {"source": "understand_query", "target": "retrieve", "type": "sequential"},
            {"source": "retrieve", "target": "search_external", "type": "sequential"},
            {"source": "search_external", "target": "add_context", "type": "sequential"},
            {"source": "add_context", "target": "format_response", "type": "sequential"},
            {"source": "format_response", "target": "__end__", "type": "sequential"}
        ]
        structure["metadata"]["total_edges"] = len(structure["edges"])
        
        # Add Navigate-specific metadata
        structure["mode_config"] = {
            "mode": "navigate",
            "llm_model": "gemini-2.0-flash-exp",
            "purpose": "Information retrieval and resource discovery",
            "agents": [
                "query_understanding_agent",
                "retrieval_agent", 
                "external_resources_agent",
                "context_agent",
                "formatting_agent"
            ]
        }
        
        print(f"  ✅ Exported {structure['metadata']['total_nodes']} nodes, {structure['metadata']['total_edges']} edges")
        return structure
    
    except Exception as e:
        print(f"  ❌ Error exporting Navigate graph: {e}")
        import traceback
        traceback.print_exc()
        return {}


def export_educate_graph() -> Dict[str, Any]:
    """Export Educate Mode graph structure."""
    print("📚 Exporting Educate Mode graph...")
    
    try:
        graph = build_educate_graph()
        structure = extract_graph_structure(graph, "educate_mode")
        
        # Manually add edges based on documented workflow
        # Educate flow: understand_query → student_model → math_translate → pedagogical_plan
        #              → generate_visualization → retrieve → [conditional] → interactive_format
        structure["edges"] = [
            {"source": "__start__", "target": "understand_query", "type": "sequential"},
            {"source": "understand_query", "target": "student_model", "type": "sequential"},
            {"source": "student_model", "target": "math_translate", "type": "sequential"},
            {"source": "math_translate", "target": "pedagogical_plan", "type": "sequential"},
            {"source": "pedagogical_plan", "target": "generate_visualization", "type": "sequential"},
            {"source": "generate_visualization", "target": "retrieve", "type": "sequential"},
            # Conditional routing after retrieval
            {"source": "retrieve", "target": "quiz_generator", "type": "conditional", "condition": "quiz_intent"},
            {"source": "retrieve", "target": "study_planner", "type": "conditional", "condition": "study_plan_intent"},
            {"source": "retrieve", "target": "add_context", "type": "conditional", "condition": "default"},
            # All paths converge
            {"source": "quiz_generator", "target": "interactive_format", "type": "sequential"},
            {"source": "study_planner", "target": "interactive_format", "type": "sequential"},
            {"source": "add_context", "target": "interactive_format", "type": "sequential"},
            {"source": "interactive_format", "target": "__end__", "type": "sequential"}
        ]
        structure["metadata"]["total_edges"] = len(structure["edges"])
        
        # Add Educate-specific metadata
        structure["mode_config"] = {
            "mode": "educate",
            "llm_model": "gemini-2.5-flash-exp",
            "purpose": "Adaptive tutoring with scaffolding and personalization",
            "agents": [
                "query_understanding_agent",
                "student_model_agent",
                "math_translation_agent",
                "pedagogical_planner_agent",
                "retrieval_agent",
                "context_agent",
                "quiz_generator_agent",
                "study_planner_agent",
                "interactive_formatting_agent"
            ],
            "conditional_routing": {
                "after_retrieval": {
                    "quiz_intent": "quiz_generator_agent",
                    "study_plan_intent": "study_planner_agent",
                    "default": "context_agent"
                }
            }
        }
        
        print(f"  ✅ Exported {structure['metadata']['total_nodes']} nodes, {structure['metadata']['total_edges']} edges")
        return structure
    
    except Exception as e:
        print(f"  ❌ Error exporting Educate graph: {e}")
        import traceback
        traceback.print_exc()
        return {}


def create_langflow_template(graph_structure: Dict[str, Any]) -> Dict[str, Any]:
    """
    Create a LangFlow-compatible JSON template from graph structure.
    
    This creates a basic template that can be imported into LangFlow
    and refined in the GUI.
    """
    graph_name = graph_structure.get("graph_name", "unknown")
    nodes = graph_structure.get("nodes", [])
    edges = graph_structure.get("edges", [])
    mode_config = graph_structure.get("mode_config", {})
    
    langflow_nodes = []
    langflow_edges = []
    
    # Convert nodes to LangFlow format
    for idx, node in enumerate(nodes):
        if node["type"] == "control":
            continue  # Skip __start__ and __end__
        
        langflow_node = {
            "id": f"node_{idx}",
            "data": {
                "type": "CustomComponent",
                "node": {
                    "template": {
                        "agent_name": {
                            "value": node["id"]
                        },
                        "description": {
                            "value": node["description"]
                        }
                    },
                    "description": node["description"],
                    "base_classes": ["Agent"],
                    "display_name": node["name"]
                }
            },
            "position": {
                "x": 100 + (idx * 200),
                "y": 100 + (idx * 50)
            },
            "type": "genericNode"
        }
        langflow_nodes.append(langflow_node)
    
    # Convert edges to LangFlow format
    for idx, edge in enumerate(edges):
        if edge["source"] in ["__start__", "__end__"] or edge["target"] in ["__start__", "__end__"]:
            continue
        
        langflow_edge = {
            "id": f"edge_{idx}",
            "source": edge["source"],
            "target": edge["target"],
            "type": edge.get("type", "sequential"),
            "condition": edge.get("condition")
        }
        langflow_edges.append(langflow_edge)
    
    return {
        "name": f"{graph_name}_flow",
        "description": mode_config.get("purpose", "LangFlow conversion from LangGraph"),
        "data": {
            "nodes": langflow_nodes,
            "edges": langflow_edges
        },
        "metadata": {
            "mode": mode_config.get("mode"),
            "llm_model": mode_config.get("llm_model"),
            "agents": mode_config.get("agents", []),
            "conditional_routing": mode_config.get("conditional_routing")
        }
    }


def main():
    """Main export function."""
    print("="*70)
    print("🔄 LangGraph to LangFlow Export Tool")
    print("="*70)
    print()
    
    # Create export directory
    export_dir = project_root / "development" / "backend" / "langflow_export"
    export_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Export directory: {export_dir}")
    print()
    
    # Export Navigate graph
    navigate_structure = export_navigate_graph()
    if navigate_structure:
        # Save raw structure
        navigate_file = export_dir / "navigate_graph.json"
        with open(navigate_file, 'w') as f:
            json.dump(navigate_structure, f, indent=2)
        print(f"  💾 Saved to: {navigate_file}")
        
        # Save LangFlow template
        navigate_template = create_langflow_template(navigate_structure)
        navigate_template_file = export_dir / "navigate_langflow_template.json"
        with open(navigate_template_file, 'w') as f:
            json.dump(navigate_template, f, indent=2)
        print(f"  📋 LangFlow template: {navigate_template_file}")
    
    print()
    
    # Export Educate graph
    educate_structure = export_educate_graph()
    if educate_structure:
        # Save raw structure
        educate_file = export_dir / "educate_graph.json"
        with open(educate_file, 'w') as f:
            json.dump(educate_structure, f, indent=2)
        print(f"  💾 Saved to: {educate_file}")
        
        # Save LangFlow template
        educate_template = create_langflow_template(educate_structure)
        educate_template_file = export_dir / "educate_langflow_template.json"
        with open(educate_template_file, 'w') as f:
            json.dump(educate_template, f, indent=2)
        print(f"  📋 LangFlow template: {educate_template_file}")
    
    print()
    
    # Create combined export summary
    summary = {
        "export_date": "2025-10-08",
        "graphs_exported": ["navigate_mode", "educate_mode"],
        "files_created": [
            "navigate_graph.json",
            "navigate_langflow_template.json",
            "educate_graph.json",
            "educate_langflow_template.json"
        ],
        "next_steps": [
            "1. Open LangFlow GUI: langflow run --port 7861",
            "2. Import templates from development/backend/langflow_export/",
            "3. Refine flows in GUI (add LLM configs, ChromaDB connections)",
            "4. Export flows to development/backend/langflow_flows/",
            "5. Integrate with FastAPI endpoints"
        ],
        "navigate_summary": {
            "nodes": navigate_structure.get("metadata", {}).get("total_nodes", 0),
            "edges": navigate_structure.get("metadata", {}).get("total_edges", 0),
            "agents": navigate_structure.get("mode_config", {}).get("agents", [])
        },
        "educate_summary": {
            "nodes": educate_structure.get("metadata", {}).get("total_nodes", 0),
            "edges": educate_structure.get("metadata", {}).get("total_edges", 0),
            "agents": educate_structure.get("mode_config", {}).get("agents", [])
        }
    }
    
    summary_file = export_dir / "export_summary.json"
    with open(summary_file, 'w') as f:
        json.dump(summary, f, indent=2)
    
    print("="*70)
    print("✅ Export Complete!")
    print(f"📊 Summary saved to: {summary_file}")
    print()
    print("🚀 Next Steps:")
    for step in summary["next_steps"]:
        print(f"   {step}")
    print()


if __name__ == "__main__":
    main()
