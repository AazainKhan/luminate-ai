#!/usr/bin/env python3
"""
Run model comparison stress test.

Usage:
    docker exec -w /app -e PYTHONPATH=/app api_brain python tests/stress/run_model_comparison.py
"""

import time
import os
import warnings
from statistics import mean, stdev

# Suppress OpenTelemetry and urllib3 warnings
warnings.filterwarnings("ignore", category=UserWarning)
os.environ["OTEL_SDK_DISABLED"] = "true"
os.environ["LANGFUSE_ENABLED"] = "false"
import logging
logging.getLogger("opentelemetry").setLevel(logging.CRITICAL)
logging.getLogger("urllib3").setLevel(logging.CRITICAL)
logging.getLogger("httpx").setLevel(logging.CRITICAL)

def run_comparison():
    print('='*80)
    print('COMPREHENSIVE MODEL COMPARISON TEST')
    print('='*80)
    
    from app.agents.supervisor import Supervisor, get_available_models
    from langchain_core.messages import HumanMessage, SystemMessage
    
    # Get available models
    print('\n📋 MODEL AVAILABILITY')
    print('-'*80)
    models = get_available_models()
    available_count = 0
    for m in models:
        status = '✅' if m['available'] else '❌'
        if m['available']:
            available_count += 1
        print(f"  {status} {m['name']:<25} | {m['provider']:<8} | {m['speed']:<10} | {m['quality']}")
    print(f'\nTotal: {available_count}/{len(models)} models available')
    
    # Initialize supervisor
    supervisor = Supervisor()
    
    # Test queries with expected characteristics
    test_queries = [
        {
            'name': 'Simple Definition',
            'query': 'What is a neural network?',
            'intent': 'fast',
            'expected_len': (100, 400),
        },
        {
            'name': 'Explanation',
            'query': 'Explain how gradient descent works to minimize loss.',
            'intent': 'explain',
            'expected_len': (200, 1200),
        },
        {
            'name': 'Tutoring (Confusion)',
            'query': "I'm really confused about how backpropagation calculates gradients. Can you help?",
            'intent': 'tutor',
            'expected_len': (300, 1500),
        },
        {
            'name': 'Code Request',
            'query': 'Write a Python function for a simple perceptron.',
            'intent': 'coder',
            'expected_len': (200, 2000),
        },
    ]
    
    # Models to test with their configurations
    models_to_test = [
        ('gemini-2.0-flash', 'Google AI', 'Recommended default'),
        ('groq-llama-70b', 'Groq', 'Ultra-fast inference'),
        ('gpt-4.1-mini', 'GitHub', 'Great for tutoring'),
    ]
    
    # Store all results
    all_results = {}
    
    # Add delay between models to avoid rate limits
    INTER_MODEL_DELAY = 3  # seconds
    INTER_QUERY_DELAY = 1.5  # seconds between queries
    
    for idx, (model_id, provider, description) in enumerate(models_to_test):
        if idx > 0:
            print(f'\n⏳ Waiting {INTER_MODEL_DELAY}s to avoid rate limits...')
            time.sleep(INTER_MODEL_DELAY)
        print(f'\n' + '='*80)
        print(f'🔍 TESTING: {model_id} ({provider})')
        print(f'   {description}')
        print('='*80)
        
        model = supervisor.get_model(model_id)
        
        times = []
        qualities = []
        lengths = []
        errors = 0
        
        for test_idx, test in enumerate(test_queries):
            # Add delay between queries to avoid rate limits
            if test_idx > 0:
                time.sleep(INTER_QUERY_DELAY)
            
            try:
                start = time.time()
                response = model.invoke([
                    SystemMessage(content='You are an AI tutor for COMP 237. Be helpful and educational.'),
                    HumanMessage(content=test['query'])
                ])
                elapsed = time.time() - start
                
                text = response.content if hasattr(response, 'content') else str(response)
                length = len(text)
                
                # Quality scoring
                min_len, max_len = test['expected_len']
                quality = 0.5
                
                # Length appropriateness
                if min_len <= length <= max_len:
                    quality += 0.25
                elif length < min_len:
                    quality += 0.1 * (length / min_len)
                else:
                    quality += 0.15  # Too long but has content
                
                # Has educational markers
                edu_markers = ['example', 'means', 'think of', 'consider', 'step']
                quality += min(0.15, sum(0.03 for m in edu_markers if m in text.lower()))
                
                # Has structure
                if any(s in text for s in ['**', '##', '- ', '1.', '`']):
                    quality += 0.1
                
                quality = min(1.0, quality)
                
                times.append(elapsed)
                qualities.append(quality)
                lengths.append(length)
                
                status = '✅' if quality >= 0.6 else '⚠️'
                print(f"  {status} {test['name']:<20} | {elapsed:>5.2f}s | {length:>5} chars | quality={quality:.2f}")
                
            except Exception as e:
                errors += 1
                print(f"  ❌ {test['name']:<20} | ERROR: {str(e)[:40]}")
        
        # Calculate stats
        if times:
            avg_time = mean(times)
            time_std = stdev(times) if len(times) > 1 else 0
            avg_quality = mean(qualities)
            avg_length = mean(lengths)
            
            all_results[model_id] = {
                'provider': provider,
                'avg_time': avg_time,
                'time_std': time_std,
                'avg_quality': avg_quality,
                'avg_length': avg_length,
                'errors': errors,
                'tests': len(test_queries),
            }
            
            print(f'\n  📊 SUMMARY:')
            print(f'     Avg Response Time: {avg_time:.2f}s (±{time_std:.2f}s)')
            print(f'     Avg Quality Score: {avg_quality:.2f}')
            print(f'     Avg Response Length: {avg_length:.0f} chars')
            print(f'     Error Rate: {errors}/{len(test_queries)}')
        else:
            all_results[model_id] = {
                'provider': provider,
                'avg_time': float('inf'),
                'avg_quality': 0,
                'errors': errors,
            }
    
    # Final Summary
    print('\n' + '='*80)
    print('🏆 FINAL COMPARISON')
    print('='*80)
    print(f"{'Model':<25} {'Provider':<10} {'Avg Time':<12} {'Quality':<10} {'Errors'}")
    print('-'*80)
    
    for model_id in sorted(all_results.keys(), key=lambda x: (-all_results[x]['avg_quality'], all_results[x]['avg_time'])):
        data = all_results[model_id]
        time_str = f"{data['avg_time']:.2f}s" if data['avg_time'] != float('inf') else 'FAILED'
        quality_str = f"{data['avg_quality']:.2f}" if data['avg_quality'] > 0 else 'N/A'
        print(f"{model_id:<25} {data['provider']:<10} {time_str:<12} {quality_str:<10} {data['errors']}/{data.get('tests', '?')}")
    
    # Recommendations
    print('\n' + '='*80)
    print('📌 RECOMMENDATIONS')
    print('='*80)
    
    working = [(k, v) for k, v in all_results.items() if v['avg_time'] != float('inf')]
    if working:
        fastest = min(working, key=lambda x: x[1]['avg_time'])
        best_quality = max(working, key=lambda x: x[1]['avg_quality'])
        
        # Calculate best balance (quality / normalized_time)
        max_time = max(v['avg_time'] for _, v in working)
        def balance_score(item):
            k, v = item
            normalized_time = v['avg_time'] / max_time
            return v['avg_quality'] / (0.5 + normalized_time)
        best_balance = max(working, key=balance_score)
        
        print(f"   ⚡ FASTEST: {fastest[0]}")
        print(f"      Average: {fastest[1]['avg_time']:.2f}s per request")
        print(f"      Best for: Quick responses, high throughput")
        print()
        print(f"   🎯 HIGHEST QUALITY: {best_quality[0]}")
        print(f"      Quality Score: {best_quality[1]['avg_quality']:.2f}")
        print(f"      Best for: Complex explanations, tutoring")
        print()
        print(f"   ⚖️  BEST BALANCE: {best_balance[0]}")
        print(f"      Time: {best_balance[1]['avg_time']:.2f}s, Quality: {best_balance[1]['avg_quality']:.2f}")
        print(f"      Best for: General use, recommended default")
    else:
        print('   ❌ No models were successfully tested!')
    
    return all_results


if __name__ == "__main__":
    run_comparison()
