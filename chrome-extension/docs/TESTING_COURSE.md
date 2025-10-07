# Testing Configuration - Course _29430_1

## Temporary Change for Testing

Since you don't currently have access to the actual COMP237 course, the extension has been configured to also inject into:

```
https://luminate.centennialcollege.ca/ultra/courses/_29430_1/*
```

## Current URL Patterns

The extension will inject the Luminate AI button on:

1. ✅ **Any COMP237 course** (when available):
   - `https://luminate.centennialcollege.ca/ultra/courses/*/outline*`
   - `https://luminate.centennialcollege.ca/ultra/courses/*/cl/outline*`

2. ✅ **Test course _29430_1** (temporary):
   - `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/*`

## How to Test

1. **Reload the extension** in Chrome:
   - Go to `chrome://extensions/`
   - Find "Luminate AI - COMP237 Course Assistant"
   - Click the **reload icon** (circular arrow)

2. **Navigate to the test course**:
   ```
   https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline
   ```

3. **Look for the button**:
   - Blue "Luminate AI" button at bottom-right
   - Should be positioned to the left of Blackboard's Help button

4. **Test the chat**:
   - Click the button to open chat interface
   - Try asking: "What is supervised learning?"
   - Make sure backend is running: `uvicorn main:app --reload`

## Important Notes

⚠️ **Content will be COMP237-specific**: Even though you're testing on a different course, the AI will still search and return COMP237 (Artificial Intelligence) content from the ChromaDB database.

This is because:
- The backend ChromaDB contains only COMP237 course materials
- The Navigate Mode agents are trained on COMP237 content
- The extension UI just provides the interface layer

## Reverting Later

When you get access to the actual COMP237 course, simply:

1. Remove the test course pattern from `manifest.json`:
   ```json
   "matches": [
     "https://luminate.centennialcollege.ca/ultra/courses/*/outline*",
     "https://luminate.centennialcollege.ca/ultra/courses/*/cl/outline*"
     // Remove: "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/*"
   ]
   ```

2. Rebuild: `npm run build`

3. Reload extension in Chrome

## What This Means

✅ **Button will inject** on course _29430_1  
✅ **Chat interface will work**  
✅ **Backend integration will work**  
✅ **Navigate Mode will search COMP237 content** (regardless of which course page you're on)

The extension just needs *a* Blackboard course page to inject into - it doesn't matter which course, since the AI content is course-specific via the backend data.

---

**Ready to test!** Navigate to the course page and you should see the Luminate AI button. 🚀
