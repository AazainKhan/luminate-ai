# 🧪 Quick Test Guide - Agent Plan

## Issues Fixed ✅

1. ✅ Backend crash: `top_results` and `external_resources` undefined
2. ✅ Double loading states in Navigate mode
3. ✅ Agent traces properly implemented (already was, but couldn't show due to crash)

---

## 🚀 Start Backend

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai/development/backend
python fastapi_service/main.py
```

**Expected output:**
```
✓ ChromaDB loaded with 917 documents
INFO:     Uvicorn running on http://127.0.0.1:8000
```

---

## 🔄 Reload Extension

1. Open Chrome: `chrome://extensions/`
2. Find **"Luminate AI"**
3. Click 🔄 **Reload** button
4. Extension should reload without errors

---

## 🧪 Test Navigate Mode

### Step 1: Open Side Panel
- Click Luminate AI extension icon in Chrome toolbar
- Side panel should open

### Step 2: Enter a Query
Try one of these:
- "Show me content about neural networks"
- "Explain gradient descent"
- "What is backpropagation?"

### Step 3: Watch the Flow

**You should see (in order):**

1. **Your message** appears on the right (blue bubble)

2. **AI response** starts appearing on the left:
   - Initially shows empty bubble
   - **Single loading indicator** (not two!)
   - Text streams in word-by-word

3. **After streaming completes:**
   - ✅ Full text response
   - ✅ Source cards (with titles and modules)
   - ✅ Related topics (blue chips)
   - ✅ **"View Agent Execution Plan (5 steps)"** - Click this!

4. **Agent Execution Plan should show:**
   - Query Understanding - "Analyzing query and extracting key terms" ✅
   - Retrieval - "Searching ChromaDB for relevant course materials" ✅  
   - External Resources - "Finding supplementary learning resources" ✅
   - Context - "Adding course structure and related topics" ✅
   - Formatting - "Generating UI-ready response with Gemini 2.0" ✅

---

## ✅ Success Criteria

- [ ] Only **ONE** loading indicator shows (not two)
- [ ] Text streams smoothly
- [ ] Source cards appear after streaming
- [ ] Related topics appear as blue chips
- [ ] **"View Agent Execution Plan"** section appears
- [ ] Clicking it shows 5 agent steps
- [ ] Each step shows "completed" status
- [ ] No backend errors in terminal
- [ ] No frontend errors in browser console

---

## 🐛 If Something Goes Wrong

### Backend Crashes
Check terminal for errors. Common issues:
```bash
# If ChromaDB not loaded
python development/backend/setup_chromadb.py

# If dependencies missing
pip install -r requirements.txt
```

### Agent Plan Not Showing
**Open Chrome DevTools (F12):**
```javascript
// Check if traces are being received
// Look for console logs showing agent traces
```

### Double Loading States
- Hard refresh: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Clear browser cache
- Reload extension again

---

## 📊 Debug Check

### Backend Stream Check:
```bash
curl -N -X POST http://localhost:8000/api/chat/navigate \
  -H "Content-Type: application/json" \
  -d '{"messages":[{"role":"user","content":"test"}],"mode":"navigate"}' \
  2>&1 | grep agent_trace
```

Should see multiple lines with `agent_trace` events.

### Frontend Console Check:
Open DevTools → Console → Look for:
- No red errors
- Messages updating with `agentTraces` array

---

## 🎯 Expected Timeline

- **Query submitted:** 0s
- **Agent traces start:** 0.1s - 0.5s
- **Text streaming starts:** 0.5s - 1s
- **Text streaming complete:** 2s - 5s
- **Agent Plan appears:** Immediately after streaming
- **Total time:** ~3-6 seconds

---

## 📝 What Changed

### Backend (`main.py`)
```python
# BEFORE (crashed):
metadata = {
    "top_results": top_results,  # ❌ Not defined
    "external_resources": external_resources  # ❌ Not defined
}

# AFTER (works):
top_results = formatted_response.get("top_results", [])
external_resources = result.get("external_resources", [])
metadata = {
    "top_results": top_results,  # ✅ Defined
    "external_resources": external_resources  # ✅ Defined
}
```

### Frontend (`NavigateMode.tsx`)
```typescript
// BEFORE (double loading):
setIsLoading(true);
// ... create message with isStreaming: true
// Both loading states active ❌

// AFTER (single loading):
// ... create message with isStreaming: true
setIsLoading(true);
// Clear loading in message_done:
setIsLoading(false); // ✅ Properly cleared
```

---

## Ready to Test! 🚀

Follow the steps above and the Agent Execution Plan should now show up properly after each query!

