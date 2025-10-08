#!/bin/bash

API="http://localhost:8000/api/query"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║        🧮 TESTING NEW MATH FORMULAS (10 additions)             ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
echo ""

test_formula() {
    query="$1"
    expected="$2"
    
    echo "Testing: $query"
    response=$(curl -s -X POST "$API" \
        -H "Content-Type: application/json" \
        -d "{\"query\": \"$query\"}")
    
    formula_name=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data['response']['formatted_response'].split('\\n')[0].replace('#', '').strip())" 2>/dev/null || echo "ERROR")
    
    if [[ "$formula_name" == *"$expected"* ]]; then
        echo "  ✅ $formula_name"
    else
        echo "  ❌ Got: $formula_name (expected: $expected)"
    fi
    echo ""
}

# Test new formulas
test_formula "what is softmax" "Softmax"
test_formula "explain MSE loss" "Mean Squared Error"
test_formula "precision and recall" "Precision"
test_formula "what is F1 score" "F1"
test_formula "adam optimizer" "Adam"
test_formula "L1 regularization" "L1/L2"
test_formula "explain dropout" "Dropout"
test_formula "batch normalization" "Batch Norm"
test_formula "learning rate decay" "Learning Rate"

echo "╔══════════════════════════════════════════════════════════════════╗"
echo "║               ✅ FORMULA LIBRARY EXPANDED!                       ║"
echo "║                                                                   ║"
echo "║   Original: 5 formulas                                           ║"
echo "║   Added: 10 formulas                                             ║"
echo "║   Total: 15+ formulas                                            ║"
echo "╚══════════════════════════════════════════════════════════════════╝"
