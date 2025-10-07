#!/usr/bin/env python3
"""Test the scope checking logic"""

# Inline the function for testing
def _is_likely_in_scope(query: str) -> bool:
    """Quick heuristic to check if query is likely about AI/ML topics."""
    query_lower = query.lower()
    
    # AI/ML related keywords
    in_scope_keywords = [
        'ai', 'artificial intelligence', 'machine learning', 'ml', 'neural network',
        'deep learning', 'agent', 'search', 'algorithm', 'supervised', 'unsupervised',
        'classification', 'regression', 'clustering', 'perceptron', 'backpropagation',
        'gradient', 'activation', 'cnn', 'rnn', 'nlp', 'computer vision', 'reinforcement',
        'training', 'model', 'prediction', 'feature', 'dataset', 'overfitting',
        'bias', 'variance', 'precision', 'recall', 'accuracy', 'loss function',
        'optimizer', 'tensorflow', 'pytorch', 'scikit', 'numpy', 'pandas',
        'assignment', 'lab', 'homework', 'comp237', 'comp 237', 'course',
        'lecture', 'tutorial', 'quiz', 'exam', 'test', 'grade'
    ]
    
    # Check if any in-scope keyword appears
    for keyword in in_scope_keywords:
        if keyword in query_lower:
            return True
    
    # Out of scope indicators
    out_of_scope_keywords = [
        'javascript', 'html', 'css', 'react', 'vue', 'angular', 'node.js',
        'database', 'sql', 'mongodb', 'web design', 'backend', 'frontend',
        'networking', 'cybersecurity', 'devops', 'cloud', 'aws', 'azure',
        'dating', 'relationship', 'health', 'medical', 'legal', 'financial',
        'cooking', 'travel', 'sports', 'music', 'movie', 'game'
    ]
    
    for keyword in out_of_scope_keywords:
        if keyword in query_lower:
            return False
    
    # Default to in-scope if uncertain
    return True

# Test cases
test_cases = [
    # In scope - AI topics
    ("What are agents?", True),
    ("Explain backpropagation", True),
    ("How do neural networks work?", True),
    ("What is supervised learning?", True),
    ("Tell me about the assignment", True),
    ("When is the comp237 exam?", True),
    
    # Out of scope - clearly not AI
    ("How do I build a React app?", False),
    ("What is SQL injection?", False),
    ("How to cook pasta?", False),
    ("Best movies of 2024?", False),
    ("Dating advice please", False),
    
    # Edge cases - should default to in-scope
    ("What is the meaning of life?", True),
    ("Random question", True),
]

print("🧪 Testing Scope Detection\n" + "="*70)
print(f"{'Query':<50} | Expected | Result | Status")
print("="*70)

passed = 0
failed = 0

for query, expected in test_cases:
    result = _is_likely_in_scope(query)
    status = "✅" if result == expected else "❌"
    
    if result == expected:
        passed += 1
    else:
        failed += 1
    
    print(f"{query:<50} | {str(expected):<8} | {str(result):<6} | {status}")

print("="*70)
print(f"\n📊 Results: {passed} passed, {failed} failed out of {len(test_cases)} tests")

if failed == 0:
    print("✅ All tests passed!")
else:
    print(f"⚠️  {failed} tests failed")
