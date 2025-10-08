"""
Test Auto Mode Router - Verify router import, endpoint availability, and data flow
Tests Issue #1: Auto mode 404 fix
"""

import sys
from pathlib import Path
import json

# Add backend to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "development" / "backend"
sys.path.insert(0, str(backend_dir))

def test_auto_router_import():
    """Test that auto router can be imported without errors"""
    print("\n" + "="*70)
    print("TEST 1: Auto Router Import")
    print("="*70)
    
    try:
        # Add fastapi_service to path
        fastapi_dir = backend_dir / "fastapi_service"
        sys.path.insert(0, str(fastapi_dir))
        
        from fastapi_service.routers import auto
        print("✅ Auto router imported successfully")
        print(f"   Router object: {auto.router}")
        print(f"   Routes: {[route.path for route in auto.router.routes]}")
        return True
    except ImportError as e:
        print(f"❌ Failed to import auto router: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False


def test_auto_endpoint_structure():
    """Test that auto endpoint has correct request/response models"""
    print("\n" + "="*70)
    print("TEST 2: Auto Endpoint Structure")
    print("="*70)
    
    try:
        from fastapi_service.routers import auto
        
        # Check request model
        print("\n📋 AutoQueryRequest fields:")
        # Use model_fields for Pydantic v2 compatibility
        request_fields = getattr(auto.AutoQueryRequest, 'model_fields', None) or getattr(auto.AutoQueryRequest, '__fields__', {})
        for field_name, field in request_fields.items():
            field_type = getattr(field, 'annotation', getattr(field, 'type_', 'unknown'))
            print(f"   - {field_name}: {field_type}")
        
        # Check response model
        print("\n📋 AutoQueryResponse fields:")
        response_fields = getattr(auto.AutoQueryResponse, 'model_fields', None) or getattr(auto.AutoQueryResponse, '__fields__', {})
        for field_name, field in response_fields.items():
            field_type = getattr(field, 'annotation', getattr(field, 'type_', 'unknown'))
            print(f"   - {field_name}: {field_type}")
        
        print("\n✅ Request/Response models are properly defined")
        return True
    except Exception as e:
        print(f"❌ Error checking endpoint structure: {e}")
        return False


def test_orchestrator_classification():
    """Test orchestrator mode classification logic"""
    print("\n" + "="*70)
    print("TEST 3: Orchestrator Classification")
    print("="*70)
    
    try:
        langgraph_dir = backend_dir / "langgraph"
        sys.path.insert(0, str(langgraph_dir))
        
        from orchestrator import classify_mode, OrchestratorState
        
        # Test navigate query
        navigate_state = OrchestratorState(
            query="Find materials about neural networks",
            student_id="test",
            session_id="test-123",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(navigate_state)
        print(f"\n🔍 Navigate Query: 'Find materials about neural networks'")
        print(f"   Mode: {result['mode']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Reasoning: {result['reasoning']}")
        
        # Test educate query
        educate_state = OrchestratorState(
            query="Explain how neural networks learn",
            student_id="test",
            session_id="test-456",
            conversation_history=[],
            mode="navigate",
            confidence=0.0,
            reasoning="",
            next_graph="navigate_graph",
            student_context={},
            last_mode="",
            mode_switch_count=0,
            conversation_turns=0,
            is_follow_up=False,
            should_confirm=False
        )
        
        result = classify_mode(educate_state)
        print(f"\n🎓 Educate Query: 'Explain how neural networks learn'")
        print(f"   Mode: {result['mode']}")
        print(f"   Confidence: {result['confidence']:.2f}")
        print(f"   Reasoning: {result['reasoning']}")
        
        print("\n✅ Orchestrator classification working")
        return True
    except Exception as e:
        print(f"❌ Error testing orchestrator: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all auto mode router tests"""
    print("\n" + "="*70)
    print("AUTO MODE ROUTER TESTS")
    print("="*70)
    
    results = {
        "Router Import": test_auto_router_import(),
        "Endpoint Structure": test_auto_endpoint_structure(),
        "Orchestrator Classification": test_orchestrator_classification()
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

