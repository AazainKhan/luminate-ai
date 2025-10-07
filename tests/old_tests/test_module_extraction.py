#!/usr/bin/env python3
"""Test the module extraction logic"""

import re

def _extract_module_from_title(title: str, original_module: str) -> str:
    """Extract a meaningful module name from the title"""
    # If module is not "Root", use it as-is
    if original_module and original_module.lower() not in ["root", "unknown", "unknown module"]:
        return original_module
    
    # Try to extract "Topic X" or "Week X" from title
    topic_match = re.search(r'Topic\s+(\d+)', title, re.IGNORECASE)
    if topic_match:
        return f"Topic {topic_match.group(1)}"
    
    week_match = re.search(r'Week\s+(\d+)', title, re.IGNORECASE)
    if week_match:
        return f"Week {week_match.group(1)}"
    
    # Check for "Lab" in title
    if re.search(r'\bLab\b', title, re.IGNORECASE):
        return "Lab Materials"
    
    # Check for "Tutorial" in title
    if re.search(r'\bTutorial\b', title, re.IGNORECASE):
        return "Tutorials"
    
    # Fallback
    return "Course Materials"

# Test cases
test_cases = [
    ("Topic 8.2: Linear classifiers", "Root"),
    ("Topic 1.3: Artificial Intelligence disciplines", "Root"),
    ("Lab Tutorial Logistic regression", "Root"),
    ("Week 5: Neural Networks", "Root"),
    ("Fairness and Bias", "Root"),
    ("Something else", "Week 3"),  # Should keep original
]

print("🧪 Testing Module Extraction\n" + "="*60)
for title, original in test_cases:
    result = _extract_module_from_title(title, original)
    print(f"Title: {title[:50]}")
    print(f"  Original: '{original}' → Extracted: '{result}'")
    print()

print("="*60)
print("✅ Test complete!")
