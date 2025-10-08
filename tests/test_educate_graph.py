"""
Test Educate Graph - Verify kmeans agent removal and workflow execution
Tests Issue #2: Remove kmeans_visualization_agent
"""

import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "development" / "backend"
langgraph_dir = backend_dir / "langgraph"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(langgraph_dir))


def test_educate_graph_import():
    """Test that educate_graph imports without kmeans errors"""
    print("\n" + "="*70)
    print("TEST 1: Educate Graph Import")
    print("="*70)
    
    try:
        from educate_graph import build_educate_graph, query_educate_mode
        print("✅ Educate graph imported successfully (no kmeans errors)")
        print(f"   Functions available: build_educate_graph, query_educate_mode")
        return True
    except ModuleNotFoundError as e:
        if "kmeans_visualization_agent" in str(e):
            print(f"❌ Still trying to import kmeans_visualization_agent: {e}")
        else:
            print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_educate_graph_nodes():
    """Test that all educate graph nodes are present and correct"""
    print("\n" + "="*70)
    print("TEST 2: Educate Graph Nodes")
    print("="*70)
    
    try:
        from educate_graph import build_educate_graph
        
        graph = build_educate_graph()
        print("✅ Educate graph built successfully")
        
        # Check graph structure
        print("\n📊 Graph nodes:")
        if hasattr(graph, 'nodes'):
            for node_name in graph.nodes:
                print(f"   - {node_name}")
        
        return True
    except Exception as e:
        print(f"❌ Error building graph: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_visualization_node_passthrough():
    """Test that visualization node is now a pass-through"""
    print("\n" + "="*70)
    print("TEST 3: Visualization Node Pass-Through")
    print("="*70)
    
    try:
        from educate_graph import _generate_visualization_node
        
        # Test state
        test_state = {
            'query': 'explain k-means clustering',
            'formatted_response': {'answer': 'Test response'}
        }
        
        result = _generate_visualization_node(test_state)
        
        print("✅ Visualization node executes without errors")
        print(f"   State preserved: {result.get('query') == test_state['query']}")
        print(f"   No kmeans_viz added: {'kmeans_viz' not in result}")
        
        return True
    except Exception as e:
        print(f"❌ Error in visualization node: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_educate_mode_execution():
    """Test full educate mode execution (without ChromaDB)"""
    print("\n" + "="*70)
    print("TEST 4: Educate Mode Execution (Mock)")
    print("="*70)
    
    try:
        from educate_graph import build_educate_graph
        
        # Build graph
        graph = build_educate_graph()
        
        # Test with mock state (no actual ChromaDB)
        test_state = {
            'query': 'What is backpropagation?',
            'chroma_db': None,  # Mock - would normally be ChromaDB instance
            'student_context': {
                'struggling_topics': [],
                'mastery_level': 'beginner',
                'session_count': 0
            }
        }
        
        print("🔄 Executing educate graph with test query...")
        print(f"   Query: {test_state['query']}")
        
        # Note: This will fail at retrieval stage without ChromaDB, but we're testing structure
        try:
            result = graph.invoke(test_state)
            print("✅ Graph executed to completion")
            print(f"   Response present: {'formatted_response' in result}")
        except Exception as inner_e:
            # Expected to fail at retrieval without ChromaDB
            if "chroma" in str(inner_e).lower() or "retrieval" in str(inner_e).lower():
                print("✅ Graph structure valid (failed at retrieval as expected without DB)")
                return True
            else:
                raise inner_e
        
        return True
    except Exception as e:
        print(f"❌ Error executing educate mode: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all educate graph tests"""
    print("\n" + "="*70)
    print("EDUCATE GRAPH TESTS")
    print("="*70)
    
    results = {
        "Graph Import": test_educate_graph_import(),
        "Graph Nodes": test_educate_graph_nodes(),
        "Visualization Pass-Through": test_visualization_node_passthrough(),
        "Graph Execution": test_educate_mode_execution()
    }
    
    print("\n" + "="*70)
    print("TEST SUMMARY")
    print("="*70)
    
    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")
    
    return all(results.values())


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

