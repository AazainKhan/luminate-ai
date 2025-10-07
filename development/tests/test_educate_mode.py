"""
Test script for Educate Mode

Run this to validate that educate mode is working correctly.
Tests all 4 intent types with sample queries.
"""

import sys
from pathlib import Path

# Add parent directories to path
project_root = Path(__file__).parent.parent
backend_dir = project_root / "development" / "backend"
langgraph_dir = backend_dir / "langgraph"

sys.path.insert(0, str(backend_dir))
sys.path.insert(0, str(langgraph_dir))

from educate_graph import query_educate_mode


def test_educate_mode():
    """Run comprehensive tests on educate mode"""
    
    print("\n" + "="*80)
    print("🧪 TESTING EDUCATE MODE")
    print("="*80 + "\n")
    
    # Test queries for each intent type
    test_cases = [
        {
            "intent": "concept",
            "query": "What is backpropagation?",
            "expected": ["definition", "explanation", "example"]
        },
        {
            "intent": "problem",
            "query": "How do I implement gradient descent in Python?",
            "expected": ["hints", "light_hint", "medium_hint", "full_solution"]
        },
        {
            "intent": "clarification",
            "query": "I'm confused about the difference between supervised and unsupervised learning",
            "expected": ["misconception", "clarification", "examples"]
        },
        {
            "intent": "assessment",
            "query": "Quiz me on neural networks",
            "expected": ["questions", "assessment"]
        }
    ]
    
    results = []
    
    for i, test in enumerate(test_cases, 1):
        print(f"\n{'─'*80}")
        print(f"Test {i}: {test['intent'].upper()} Intent")
        print(f"{'─'*80}")
        print(f"Query: {test['query']}\n")
        
        try:
            # Run educate mode
            result = query_educate_mode(test['query'])
            
            # Extract data
            formatted = result.get('formatted_response', {})
            metadata = result.get('metadata', {})
            
            # Validate
            success = True
            issues = []
            
            # Check intent classification
            detected_intent = metadata.get('intent', 'unknown')
            if detected_intent != test['intent']:
                issues.append(f"❌ Intent mismatch: expected '{test['intent']}', got '{detected_intent}'")
                success = False
            else:
                print(f"✅ Intent correctly classified: {detected_intent}")
            
            # Check response content
            main_content = formatted.get('main_content', '')
            if not main_content or len(main_content) < 50:
                issues.append(f"❌ Main content too short: {len(main_content)} chars")
                success = False
            else:
                print(f"✅ Main content generated: {len(main_content)} chars")
            
            # Check intent-specific features
            if test['intent'] == 'problem':
                if 'hints' in formatted and formatted['hints']:
                    print(f"✅ Scaffolded hints provided")
                else:
                    issues.append(f"❌ No hints for problem-solving")
                    success = False
            
            if test['intent'] == 'assessment':
                if 'assessment_questions' in formatted and formatted['assessment_questions']:
                    print(f"✅ Assessment questions generated: {len(formatted['assessment_questions'])}")
                else:
                    issues.append(f"❌ No assessment questions")
                    success = False
            
            # Check Socratic questions (optional but nice to have)
            if 'socratic_questions' in formatted and formatted['socratic_questions']:
                print(f"✅ Socratic questions included: {len(formatted['socratic_questions'])}")
            
            # Check sources
            sources = formatted.get('sources', [])
            print(f"✅ Sources from ChromaDB: {len(sources)}")
            
            # Display response preview
            print(f"\n📝 Response Preview:")
            print(f"{main_content[:300]}...")
            
            if issues:
                print(f"\n⚠️  Issues found:")
                for issue in issues:
                    print(f"  {issue}")
            
            results.append({
                'test': test['intent'],
                'success': success,
                'issues': issues
            })
            
        except Exception as e:
            print(f"\n❌ ERROR: {e}")
            import traceback
            traceback.print_exc()
            results.append({
                'test': test['intent'],
                'success': False,
                'issues': [str(e)]
            })
    
    # Summary
    print(f"\n{'='*80}")
    print("📊 TEST SUMMARY")
    print(f"{'='*80}\n")
    
    passed = sum(1 for r in results if r['success'])
    total = len(results)
    
    print(f"Tests Passed: {passed}/{total}")
    
    for result in results:
        status = "✅ PASS" if result['success'] else "❌ FAIL"
        print(f"  {status} - {result['test'].upper()}")
        if result['issues']:
            for issue in result['issues']:
                print(f"    → {issue}")
    
    print(f"\n{'='*80}\n")
    
    if passed == total:
        print("🎉 All tests passed! Educate mode is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the issues above.")
        return False


def quick_test():
    """Quick single test"""
    print("\n🚀 Quick Test - Concept Explanation\n")
    
    result = query_educate_mode("What is machine learning?")
    
    formatted = result.get('formatted_response', {})
    metadata = result.get('metadata', {})
    
    print(f"Intent: {metadata.get('intent')}")
    print(f"Response Type: {formatted.get('response_type')}")
    print(f"Content Length: {len(formatted.get('main_content', ''))} chars")
    print(f"Sources: {len(formatted.get('sources', []))}")
    print(f"\nResponse:\n{formatted.get('main_content', 'No content')}\n")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Test Educate Mode")
    parser.add_argument('--quick', action='store_true', help='Run quick test only')
    args = parser.parse_args()
    
    try:
        if args.quick:
            quick_test()
        else:
            success = test_educate_mode()
            sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
