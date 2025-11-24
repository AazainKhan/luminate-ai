#!/bin/bash

echo "🧪 QUICK AGENT TEST SUITE"
echo "=" 
echo ""

queries=(
    "What is COMP 237?"
    "What are the learning outcomes?"
    "Explain backpropagation"
    "Write code for Assignment 1"
    "What's the weather today?"
)

for query in "${queries[@]}"; do
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "Query: $query"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    
    docker compose exec -T api_brain python -c "
from app.agents.tutor_agent import run_agent
result = run_agent('$query', 'test_user', 'test@my.centennialcollege.ca')
print(f'Response: {result.get(\"response\", \"\")[:300]}...')
print(f'Intent: {result.get(\"intent\")}')
print(f'Model: {result.get(\"model_used\")}')
print(f'Sources: {len(result.get(\"sources\", []))}')
if result.get(\"error\"):
    print(f'❌ Error: {result.get(\"error\")}')
" 2>&1 | grep -E "Response:|Intent:|Model:|Sources:|Error:"
    
    echo ""
done

echo "✅ Test suite complete!"

