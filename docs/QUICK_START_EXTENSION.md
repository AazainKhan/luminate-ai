# 🚀 Quick Start Guide - Luminate AI Chrome Extension

## Prerequisites

- ✅ Backend setup complete (ChromaDB + FastAPI + LangGraph)
- ✅ Node.js installed (v18 or higher)
- ✅ Chrome browser
- ✅ Git repository cloned

## 5-Minute Setup

### Step 1: Build the Extension (2 minutes)

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai/chrome-extension
npm install
npm run build
```

**Expected Output:**
```
✓ 1574 modules transformed.
dist/popup.html       0.42 kB
dist/popup.css       14.43 kB
dist/popup.js         5.21 kB
dist/content.js       8.06 kB
dist/background.js    0.25 kB
✓ built in 1.16s
```

### Step 2: Load Extension in Chrome (1 minute)

1. Open Chrome
2. Navigate to: `chrome://extensions/`
3. Toggle **Developer mode** (top-right)
4. Click **Load unpacked**
5. Select folder: `/Users/aazain/Documents/GitHub/luminate-ai/chrome-extension/dist`

**Success Indicator:** Luminate AI appears in extensions list

### Step 3: Start Backend (1 minute)

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai/development/backend/fastapi_service
source ../../../.venv/bin/activate
uvicorn main:app --reload
```

**Expected Output:**
```
🚀 Starting Luminate AI FastAPI service...
✓ ChromaDB loaded with 917 documents
✓ LangGraph Navigate workflow initialized
INFO:     Application startup complete.
INFO:     Uvicorn running on http://127.0.0.1:8000
```

### Step 4: Test It! (1 minute)

1. Navigate to COMP237 course page:
   ```
   https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline
   ```

2. Look for blue **Luminate AI** button (bottom-right, left of Help button)

3. Click button → Chat opens

4. Ask: "What is supervised learning?"

5. Wait 5 seconds → See formatted response with related topics

**Success Indicator:** Chat shows response with top results and related topics

---

## Troubleshooting

### Extension Not Loading?

**Check:**
```bash
# Verify dist/ folder exists
ls -la chrome-extension/dist/

# Should show: manifest.json, popup.html, *.js, *.css
```

**Fix:**
```bash
cd chrome-extension
rm -rf dist/
npm run build
# Then reload extension in chrome://extensions/
```

### Backend Not Starting?

**Check:**
```bash
# Verify virtual environment
source .venv/bin/activate
which python  # Should show .venv path

# Check ChromaDB
ls -la development/backend/chroma_db/
# Should have files (not empty)
```

**Fix:**
```bash
# Reinstall dependencies
cd development/backend
pip install -r requirements.txt

# Verify ChromaDB setup
python setup_chromadb.py
```

### Button Not Appearing?

**Check:**
1. Are you on correct URL? `*/ultra/courses/*/outline*`
2. Open browser console (F12) → Check for errors
3. Extension enabled in `chrome://extensions/`?

**Fix:**
```bash
# Reload extension
# In chrome://extensions/, click reload icon

# Check content script injection
# Open DevTools → Sources → Content scripts → luminate-ai-extension
```

### API Errors?

**Check:**
```bash
# Test backend health
curl http://localhost:8000/health

# Should return: {"status":"healthy","chromadb_documents":917}
```

**Fix:**
```bash
# Restart backend
# Ctrl+C to stop
uvicorn main:app --reload
```

---

## Development Workflow

### Making Changes

1. **Edit React components** in `chrome-extension/src/`
2. **Rebuild**: `npm run build`
3. **Reload extension**: Click reload in `chrome://extensions/`
4. **Test**: Refresh Blackboard page

### Watch Mode (Auto-rebuild)

```bash
cd chrome-extension
npm run watch
```

Now changes auto-rebuild (but still need to reload extension manually)

---

## Quick Test Script

```bash
# Test LangGraph endpoint
cd /Users/aazain/Documents/GitHub/luminate-ai
python test_langgraph_endpoint.py
```

**Expected Output:**
```
🧪 Testing Luminate AI LangGraph Navigate Endpoint
🏥 Testing /health endpoint...
✓ Health check passed
  ChromaDB documents: 917

🤖 Testing /langgraph/navigate with query: 'What is supervised learning?'
✓ LangGraph Navigate succeeded (4523ms)

📝 Formatted Response:
Supervised learning is a machine learning approach...

📚 Top Results: 10
  1. Machine Learning Basics
     💡 This result explains the fundamentals of supervised learning

🔗 Related Topics: Classification, Regression, Neural Networks

✅ All tests completed!
```

---

## Next Steps

1. **Customize UI**: Edit colors in `chrome-extension/tailwind.config.js`
2. **Add Features**: Implement session persistence, keyboard shortcuts
3. **Test Queries**: Try different questions, explore related topics
4. **Collect Feedback**: Share with classmates, gather insights

---

## Key Files to Know

```
chrome-extension/
├── src/
│   ├── popup/Popup.tsx          # Extension menu
│   ├── content/index.tsx        # Sticky button
│   ├── components/ChatInterface.tsx  # Chat UI
│   └── services/api.ts          # Backend API calls

development/backend/fastapi_service/
└── main.py                      # FastAPI endpoints (includes /langgraph/navigate)
```

---

## Support

**Documentation:**
- Chrome Extension: `chrome-extension/README.md`
- Navigate Mode: `NAVIGATE_MODE_COMPLETE.md`
- LLM Config: `LLM_CONFIGURATION.md`

**Logs:**
- Backend: `development/backend/logs/fastapi_service.log`
- Extension: Chrome DevTools Console (F12)

---

**🎉 You're all set! Happy learning with Luminate AI! 🎉**
