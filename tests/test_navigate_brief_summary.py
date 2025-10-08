"""
Test Navigate Brief Summary - Verify brief_summary field in responses
Tests Issue #4: Add brief description to Navigate mode
"""

import sys
from pathlib import Path
import json

# Add backend to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "development" / "backend"
langgraph_dir = backend_dir / "langgraph"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(langgraph_dir))


def test_formatting_prompt_has_brief_summary():
    """Test that formatting prompt includes brief_summary field"""
    print("\n" + "="*70)
    print("TEST 1: Formatting Prompt Structure")
    print("="*70)
    
    try:
        from agents.formatting import FORMATTING_PROMPT
        
        print("📝 Checking FORMATTING_PROMPT...")
        
        if "brief_summary" in FORMATTING_PROMPT:
            print("✅ FORMATTING_PROMPT includes 'brief_summary' field")
            
            # Show relevant section
            lines = FORMATTING_PROMPT.split('\n')
            for i, line in enumerate(lines):
                if 'brief_summary' in line.lower():
                    context_start = max(0, i - 2)
                    context_end = min(len(lines), i + 3)
                    print("\n   Context around brief_summary:")
                    for j in range(context_start, context_end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{lines[j]}")
                    break
            return True
        else:
            print("❌ FORMATTING_PROMPT missing 'brief_summary' field")
            return False
    except Exception as e:
        print(f"❌ Error checking formatting prompt: {e}")
        return False


def test_formatting_agent_fallback():
    """Test that fallback responses include brief_summary"""
    print("\n" + "="*70)
    print("TEST 2: Fallback Response Structure")
    print("="*70)
    
    try:
        from agents.formatting import formatting_agent
        
        # Test with empty results (triggers fallback)
        test_state_in_scope = {
            "query": "explain neural networks",
            "enriched_results": [],
            "external_resources": []
        }
        
        print("🔍 Testing in-scope fallback...")
        result = formatting_agent(test_state_in_scope)
        
        formatted_response = result.get("formatted_response", {})
        
        if "brief_summary" in formatted_response:
            print(f"✅ In-scope fallback includes brief_summary")
            print(f"   Value: '{formatted_response['brief_summary']}'")
        else:
            print(f"❌ In-scope fallback missing brief_summary")
            print(f"   Keys present: {list(formatted_response.keys())}")
            return False
        
        # Test out-of-scope
        test_state_out_scope = {
            "query": "how to cook pasta",
            "enriched_results": [],
            "external_resources": []
        }
        
        print("\n🔍 Testing out-of-scope fallback...")
        result = formatting_agent(test_state_out_scope)
        
        formatted_response = result.get("formatted_response", {})
        
        if "brief_summary" in formatted_response:
            print(f"✅ Out-of-scope fallback includes brief_summary")
            print(f"   Value: '{formatted_response['brief_summary']}'")
        else:
            print(f"❌ Out-of-scope fallback missing brief_summary")
            return False
        
        return True
    except Exception as e:
        print(f"❌ Error testing fallback: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_auto_router_includes_brief_summary():
    """Test that auto router includes brief_summary in response_data"""
    print("\n" + "="*70)
    print("TEST 3: Auto Router Response Data")
    print("="*70)
    
    try:
        # Read the auto.py file to verify code structure
        auto_file = backend_dir / "fastapi_service" / "routers" / "auto.py"
        
        with open(auto_file, 'r') as f:
            content = f.read()
        
        # Check for brief_summary in navigate mode response_data
        if '"brief_summary":' in content:
            print("✅ auto.py includes brief_summary in response_data")
            
            # Find and show the relevant code section
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if 'brief_summary' in line and 'response_data' in content[max(0, content.rfind('{', 0, content.index(line))):content.index(line)+200]:
                    print(f"\n   Found at line {i+1}:")
                    context_start = max(0, i - 3)
                    context_end = min(len(lines), i + 4)
                    for j in range(context_start, context_end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{lines[j]}")
                    break
            return True
        else:
            print("❌ auto.py missing brief_summary in response_data")
            return False
    except Exception as e:
        print(f"❌ Error checking auto router: {e}")
        return False


def test_navigate_response_structure():
    """Test complete navigate response structure with brief_summary"""
    print("\n" + "="*70)
    print("TEST 4: Navigate Response Structure")
    print("="*70)
    
    try:
        from agents.formatting import formatting_agent
        
        # Mock enriched results with content
        test_state = {
            "query": "What is gradient descent?",
            "enriched_results": [
                {
                    "content": "Gradient descent is an optimization algorithm used to minimize loss functions.",
                    "metadata": {
                        "title": "Gradient Descent Tutorial",
                        "module": "Week 3",
                        "live_lms_url": "https://example.com"
                    },
                    "score": 0.95
                }
            ],
            "external_resources": []
        }
        
        print("🔄 Processing test query with formatting agent...")
        result = formatting_agent(test_state)
        
        formatted_response = result.get("formatted_response", {})
        
        print("\n📋 Response structure:")
        required_fields = ["brief_summary", "answer", "is_in_scope", "top_results", "related_topics"]
        
        all_present = True
        for field in required_fields:
            present = field in formatted_response
            status = "✅" if present else "❌"
            print(f"   {status} {field}: {present}")
            if not present:
                all_present = False
        
        if all_present:
            print("\n✅ All required fields present in response")
            if formatted_response.get("brief_summary"):
                print(f"   Brief summary preview: '{formatted_response['brief_summary'][:80]}...'")
            return True
        else:
            print("\n❌ Missing required fields")
            return False
            
    except Exception as e:
        print(f"❌ Error testing response structure: {e}")
        import traceback
        traceback.print_exc()
        return False


def run_all_tests():
    """Run all brief summary tests"""
    print("\n" + "="*70)
    print("NAVIGATE BRIEF SUMMARY TESTS")
    print("="*70)
    
    results = {
        "Formatting Prompt": test_formatting_prompt_has_brief_summary(),
        "Fallback Responses": test_formatting_agent_fallback(),
        "Auto Router Integration": test_auto_router_includes_brief_summary(),
        "Response Structure": test_navigate_response_structure()
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

