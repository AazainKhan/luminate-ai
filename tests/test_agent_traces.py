"""
Test Agent Traces - Verify trace collection and data flow
Tests Issue #5: Real-time agent execution traces
"""

import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "development" / "backend"
langgraph_dir = backend_dir / "langgraph"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(langgraph_dir))


def test_navigate_graph_has_trace_support():
    """Test that navigate_graph has trace callback infrastructure"""
    print("\n" + "="*70)
    print("TEST 1: Navigate Graph Trace Support")
    print("="*70)
    
    try:
        from navigate_graph import build_navigate_graph, _wrap_agent_with_trace
        
        print("✅ Navigate graph imported with trace support")
        print(f"   _wrap_agent_with_trace function available")
        
        # Test trace wrapper
        test_traces = []
        def test_callback(trace):
            test_traces.append(trace)
        
        def dummy_agent(state):
            return state
        
        wrapped = _wrap_agent_with_trace(dummy_agent, "test_agent", "Testing trace wrapper")
        
        test_state = {"trace_callback": test_callback, "query": "test"}
        wrapped(test_state)
        
        if len(test_traces) >= 2:  # Should have start and end traces
            print(f"✅ Trace wrapper working (captured {len(test_traces)} traces)")
            print(f"   Sample trace: {test_traces[0]}")
            return True
        else:
            print(f"❌ Trace wrapper not capturing traces properly")
            return False
            
    except Exception as e:
        print(f"❌ Error testing trace support: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_router_trace_collection():
    """Test that auto router collects traces for navigate mode"""
    print("\n" + "="*70)
    print("TEST 2: Auto Router Trace Collection")
    print("="*70)
    
    try:
        # Read auto.py to verify trace collection code
        auto_file = backend_dir / "fastapi_service" / "routers" / "auto.py"
        
        with open(auto_file, 'r') as f:
            content = f.read()
        
        # Check for trace_callback in navigate mode
        has_trace_callback = "trace_callback" in content
        has_agent_traces = "agent_traces" in content
        has_trace_append = "agent_traces.append" in content or "agent_traces = []" in content
        
        print(f"   trace_callback present: {has_trace_callback}")
        print(f"   agent_traces variable: {has_agent_traces}")
        print(f"   trace collection logic: {has_trace_append}")
        
        if has_trace_callback and has_agent_traces:
            print("✅ Auto router has trace collection infrastructure")
            
            # Show code snippet
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'def trace_callback' in line:
                    print(f"\n   Found trace_callback at line {i+1}:")
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 8)
                    for j in range(context_start, context_end):
                        print(f"    {lines[j]}")
                    break
            return True
        else:
            print("❌ Auto router missing trace collection")
            return False
            
    except Exception as e:
        print(f"❌ Error checking auto router: {e}")
        return False


def test_trace_data_in_response():
    """Test that agent_traces is included in response_data"""
    print("\n" + "="*70)
    print("TEST 3: Traces in Response Data")
    print("="*70)
    
    try:
        auto_file = backend_dir / "fastapi_service" / "routers" / "auto.py"
        
        with open(auto_file, 'r') as f:
            content = f.read()
        
        # Check if agent_traces is added to response_data for both modes
        navigate_has_traces = '"agent_traces": agent_traces' in content
        educate_has_traces = '"agent_traces": []' in content  # Placeholder for educate
        
        print(f"   Navigate mode includes agent_traces: {navigate_has_traces}")
        print(f"   Educate mode includes agent_traces: {educate_has_traces}")
        
        if navigate_has_traces and educate_has_traces:
            print("✅ Both modes include agent_traces in response_data")
            return True
        else:
            print("❌ Missing agent_traces in response_data")
            return False
            
    except Exception as e:
        print(f"❌ Error checking response data: {e}")
        return False


def test_trace_format():
    """Test that trace format matches expected structure"""
    print("\n" + "="*70)
    print("TEST 4: Trace Format")
    print("="*70)
    
    try:
        from navigate_graph import _wrap_agent_with_trace
        from datetime import datetime
        
        traces = []
        def callback(trace):
            traces.append(trace)
        
        def test_agent(state):
            return {**state, "test": "value"}
        
        wrapped = _wrap_agent_with_trace(test_agent, "test_agent", "Performing test action")
        
        state = {"trace_callback": callback}
        wrapped(state)
        
        print(f"   Captured {len(traces)} traces")
        
        if traces:
            trace = traces[0]
            print(f"\n   Trace structure:")
            print(f"      agent: {trace.get('agent')}")
            print(f"      action: {trace.get('action')}")
            print(f"      status: {trace.get('status')}")
            print(f"      timestamp: {trace.get('timestamp')}")
            
            required_fields = ['agent', 'action', 'status', 'timestamp']
            has_all_fields = all(field in trace for field in required_fields)
            
            if has_all_fields:
                print("\n✅ Trace format correct with all required fields")
                return True
            else:
                print("\n❌ Trace missing required fields")
                return False
        else:
            print("❌ No traces captured")
            return False
            
    except Exception as e:
        print(f"❌ Error testing trace format: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all agent trace tests"""
    print("\n" + "="*70)
    print("AGENT TRACE TESTS")
    print("="*70)
    
    results = {
        "Navigate Graph Trace Support": test_navigate_graph_has_trace_support(),
        "Auto Router Trace Collection": test_auto_router_trace_collection(),
        "Traces in Response Data": test_trace_data_in_response(),
        "Trace Format": test_trace_format()
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

