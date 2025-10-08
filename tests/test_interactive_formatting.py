"""
Test Interactive Formatting - Verify no placeholder text and proper structure
Tests Issue #2 & #3c: Educate mode formatting improvements
"""

import sys
from pathlib import Path

# Add backend to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "development" / "backend"
langgraph_dir = backend_dir / "langgraph"
sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(langgraph_dir))


def test_no_placeholder_text():
    """Test that interactive formatting has no placeholder text"""
    print("\n" + "="*70)
    print("TEST 1: No Placeholder Text")
    print("="*70)
    
    try:
        formatting_file = langgraph_dir / "agents" / "interactive_formatting.py"
        
        with open(formatting_file, 'r') as f:
            content = f.read()
        
        # Check for common placeholder phrases
        placeholders = [
            "Let me help you with",
            "Let me help you understand",
            "I'll help you",
            "placeholder"
        ]
        
        found_placeholders = []
        for placeholder in placeholders:
            if placeholder.lower() in content.lower():
                found_placeholders.append(placeholder)
        
        if not found_placeholders:
            print("✅ No placeholder text found")
            return True
        else:
            print(f"❌ Found placeholder text: {found_placeholders}")
            
            # Show context
            lines = content.split('\n')
            for placeholder in found_placeholders:
                for i, line in enumerate(lines):
                    if placeholder.lower() in line.lower():
                        print(f"\n   Found at line {i+1}:")
                        print(f"    {line.strip()}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking for placeholders: {e}")
        return False


def test_fallback_interactive_structure():
    """Test that fallback_interactive has proper structure"""
    print("\n" + "="*70)
    print("TEST 2: Fallback Interactive Structure")
    print("="*70)
    
    try:
        from agents.interactive_formatting import _fallback_interactive
        
        # Test with mock data
        test_state = {
            "query": "What is backpropagation?",
            "enriched_results": [
                {
                    "content": "Backpropagation is an algorithm for training neural networks...",
                    "metadata": {
                        "title": "Neural Networks Basics",
                        "module": "Week 5"
                    }
                }
            ]
        }
        
        result = _fallback_interactive(test_state)
        formatted = result.get("formatted_response", {})
        
        print(f"\n   Checking response structure...")
        
        required_fields = ["type", "interaction_type", "answer", "content", "sections", "follow_up_prompts", "sources"]
        missing_fields = [f for f in required_fields if f not in formatted]
        
        if not missing_fields:
            print(f"✅ All required fields present")
            print(f"   - type: {formatted['type']}")
            print(f"   - interaction_type: {formatted['interaction_type']}")
            print(f"   - answer length: {len(formatted['answer'])} chars")
            print(f"   - content length: {len(formatted['content'])} chars")
            print(f"   - sections: {len(formatted['sections'])}")
            
            # Check that answer and content are not empty or generic
            if len(formatted['answer']) > 20 and len(formatted['content']) > 20:
                print(f"✅ Answer and content have substantial text")
                return True
            else:
                print(f"❌ Answer or content too short")
                return False
        else:
            print(f"❌ Missing fields: {missing_fields}")
            return False
            
    except Exception as e:
        print(f"❌ Error testing fallback structure: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_all_formatting_functions_have_answer():
    """Test that all formatting functions return answer/content fields"""
    print("\n" + "="*70)
    print("TEST 3: All Formatters Have Answer Field")
    print("="*70)
    
    try:
        from agents.interactive_formatting import (
            _format_scaffolded_hints,
            _format_direct_explanation,
            _fallback_interactive
        )
        
        formatters = [
            ("scaffolded_hints", _format_scaffolded_hints),
            ("direct_explanation", _format_direct_explanation),
            ("fallback", _fallback_interactive)
        ]
        
        test_query = "Explain gradient descent"
        test_prompts = {
            "intro": "Let's explore this concept",
            "initial_question": "What do you think gradient descent is?",
            "hints": {
                "hint_1": "Think about minimizing functions",
                "hint_2": "Consider the slope of a curve",
                "hint_3": "It's about finding the minimum point"
            }
        }
        test_results = [
            {
                "content": "Gradient descent is an optimization algorithm...",
                "metadata": {"title": "ML Basics", "module": "Week 3"}
            }
        ]
        
        all_pass = True
        
        for name, formatter in formatters:
            print(f"\n   Testing {name}...")
            
            try:
                if name == "scaffolded_hints":
                    response = formatter(test_query, test_prompts, test_results)
                elif name == "direct_explanation":
                    test_prompts_explain = {
                        "definition": "Gradient descent optimizes by following gradients",
                        "importance": "Essential for training neural networks",
                        "how_it_works": "Iteratively updates parameters",
                        "example": "Used in backpropagation",
                        "common_mistakes": ["Learning rate too high", "Not normalizing data"]
                    }
                    response = formatter(test_query, test_prompts_explain, test_results)
                else:  # fallback
                    test_state = {"query": test_query, "enriched_results": test_results}
                    result = formatter(test_state)
                    response = result.get("formatted_response", {})
                
                has_answer = "answer" in response
                has_content = "content" in response
                
                if has_answer and has_content:
                    print(f"      ✅ Has answer and content fields")
                    print(f"         Answer length: {len(response['answer'])} chars")
                    print(f"         Content length: {len(response['content'])} chars")
                else:
                    print(f"      ❌ Missing answer or content")
                    print(f"         Has answer: {has_answer}, Has content: {has_content}")
                    all_pass = False
                    
            except Exception as e:
                print(f"      ❌ Error: {e}")
                all_pass = False
        
        return all_pass
        
    except Exception as e:
        print(f"❌ Error testing formatters: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_interaction_types():
    """Test that all interaction types are properly defined"""
    print("\n" + "="*70)
    print("TEST 4: Interaction Types")
    print("="*70)
    
    try:
        formatting_file = langgraph_dir / "agents" / "interactive_formatting.py"
        
        with open(formatting_file, 'r') as f:
            content = f.read()
        
        expected_types = [
            "scaffolded_hints",
            "quiz",
            "worked_example",
            "socratic_dialogue",
            "concept_map",
            "direct_explanation"
        ]
        
        print("   Checking for interaction types...")
        
        found_types = []
        for itype in expected_types:
            if f'interaction_type": "{itype}"' in content or f"interaction_type': '{itype}'" in content:
                found_types.append(itype)
                print(f"      ✅ {itype}")
        
        missing_types = set(expected_types) - set(found_types)
        
        if not missing_types:
            print(f"\n✅ All {len(expected_types)} interaction types present")
            return True
        else:
            print(f"\n❌ Missing interaction types: {missing_types}")
            return False
            
    except Exception as e:
        print(f"❌ Error checking interaction types: {e}")
        return False


def run_all_tests():
    """Run all interactive formatting tests"""
    print("\n" + "="*70)
    print("INTERACTIVE FORMATTING TESTS")
    print("="*70)
    
    results = {
        "No Placeholder Text": test_no_placeholder_text(),
        "Fallback Structure": test_fallback_interactive_structure(),
        "All Formatters Have Answer": test_all_formatting_functions_have_answer(),
        "Interaction Types": test_interaction_types()
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

