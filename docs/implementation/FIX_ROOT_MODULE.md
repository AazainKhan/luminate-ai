# Fixed: "Root" Module Issue

## What is "Root"?

**"Root"** in Blackboard means content that exists at the **top level** of the course, not organized into specific week folders or module sections. 

In your COMP237 course export, **ALL 117 content items** have `"module": "Root"` because the Blackboard course structure doesn't use organized week/module folders.

## The Problem

When you asked questions, every result showed:
```
Related Course Content:
- Topic 8.2: Linear classifiers (Root) ❌
- Topic 1.3: AI disciplines (Root) ❌
- Lab Tutorial (Root) ❌
```

This was confusing and not helpful!

## The Solution

I created a **smart module extraction function** that reads the **title** instead of relying on the "Root" value. It extracts meaningful organization from the content titles:

### Extraction Rules:

1. **"Topic X.Y: ..." → "Topic X"**
   - `"Topic 8.2: Linear classifiers"` → `Topic 8`
   - `"Topic 1.3: AI disciplines"` → `Topic 1`

2. **"Week X: ..." → "Week X"**
   - `"Week 5: Neural Networks"` → `Week 5`

3. **Contains "Lab" → "Lab Materials"**
   - `"Lab Tutorial Logistic regression"` → `Lab Materials`

4. **Contains "Tutorial" → "Tutorials"**
   - `"Tutorial: Agents"` → `Tutorials`

5. **Fallback → "Course Materials"**
   - `"Fairness and Bias"` → `Course Materials`

## Expected Behavior Now

### Before:
```
Related Course Content:
- Topic 8.2: Linear classifiers (Root)
- Topic 1.3: AI disciplines (Root)
- Lab Tutorial (Root)
```

### After:
```
Related Course Content:
- Topic 8.2: Linear classifiers (Topic 8)
- Topic 1.3: AI disciplines (Topic 1)
- Lab Tutorial Logistic regression (Lab Materials)
```

## Code Changes

### File: `development/backend/langgraph/agents/formatting.py`

Added new function `_extract_module_from_title()`:
```python
def _extract_module_from_title(title: str, original_module: str) -> str:
    """
    Extract a meaningful module name from the title if the original module is 'Root'.
    
    Examples:
        "Topic 8.2: Linear classifiers" → "Topic 8"
        "Lab Tutorial" → "Lab Materials"
        "Fairness and Bias" → "Course Materials"
    """
    import re
    
    # If module is not "Root", use it as-is
    if original_module.lower() not in ["root", "unknown"]:
        return original_module
    
    # Try to extract "Topic X" from title
    topic_match = re.search(r'Topic\s+(\d+)', title, re.IGNORECASE)
    if topic_match:
        return f"Topic {topic_match.group(1)}"
    
    # Try to extract "Week X" from title
    week_match = re.search(r'Week\s+(\d+)', title, re.IGNORECASE)
    if week_match:
        return f"Week {week_match.group(1)}"
    
    # Check for "Lab" or "Tutorial"
    if re.search(r'\bLab\b', title, re.IGNORECASE):
        return "Lab Materials"
    if re.search(r'\bTutorial\b', title, re.IGNORECASE):
        return "Tutorials"
    
    # Fallback
    return "Course Materials"
```

Updated 3 places to use this function:
1. `_prepare_results_summary()` - For LLM prompt
2. `_fallback_formatting()` - For fallback responses
3. Related topics filtering - Exclude generic modules

## Testing

Tested with actual course data:
```
✅ "Topic 8.2: Linear classifiers" → Topic 8
✅ "Topic 1.3: AI disciplines" → Topic 1
✅ "Lab Tutorial Logistic regression" → Lab Materials
✅ "Week 5: Neural Networks" → Week 5
✅ "Fairness and Bias" → Course Materials
```

## How to Apply

**You need to restart the backend server:**

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai/development/backend
source ../../.venv/bin/activate
python fastapi_service/main.py
```

Once restarted, you'll see meaningful module names instead of "Root"!

## Files Modified

- ✅ `development/backend/langgraph/agents/formatting.py`
  - Added `_extract_module_from_title()` function
  - Updated `_prepare_results_summary()` to extract modules
  - Updated `_fallback_formatting()` to extract modules
  - Improved related topics filtering

## Summary

**Root** wasn't an error - it's Blackboard's way of saying "top-level content not in folders". But now the system is smart enough to extract **meaningful organization** from the content titles themselves, giving you helpful context like "Topic 8", "Lab Materials", or "Tutorials" instead of the confusing "Root"! 🎉
