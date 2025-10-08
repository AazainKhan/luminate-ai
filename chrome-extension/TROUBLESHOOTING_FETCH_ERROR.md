# 🔧 Troubleshooting Guide: "Failed to fetch" Error

## ❌ Error Message
```
Unified query error: TypeError: Failed to fetch
```

## 🎯 What This Means
The Chrome extension cannot connect to the Luminate AI backend server at `http://localhost:8000`.

---

## ✅ Solution Steps (Follow in Order)

### **Step 1: Start the Backend Server**

```bash
# Navigate to backend directory
cd /Users/aazain/Documents/GitHub/luminate-ai/development/backend

# Activate virtual environment
source ../../.venv/bin/activate

# Start the FastAPI server
python fastapi_service/main.py
```

**Expected Output:**
```
INFO:     Started server process [xxxxx]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

**Verify Backend is Running:**
```bash
curl http://localhost:8000/docs
# Should return HTML for Swagger UI
```

---

### **Step 2: Reload the Chrome Extension**

**CRITICAL:** Extensions cache their code. You MUST reload after building.

1. Open Chrome: `chrome://extensions/`
2. Find "Luminate AI - COMP237 Course Assistant"
3. Click the **🔄 Reload** button
4. ✅ Status should show: "Service worker (active)"

---

### **Step 3: Verify Permissions**

**Check manifest.json has:**
```json
{
  "host_permissions": [
    "http://localhost:8000/*"
  ]
}
```

**If missing:**
```bash
cd chrome-extension
npm run build
# Then reload extension (Step 2)
```

---

### **Step 4: Test Backend Connection**

**Open Chrome DevTools:**
1. Right-click extension side panel
2. Select "Inspect"
3. Go to **Console** tab

**Expected logs when you send a message:**
```
🔵 Making unified query to: http://localhost:8000/api/query
✅ Unified query response: {mode: "educate", confidence: 0.8, ...}
```

**If you see:**
```
❌ Unified query error: TypeError: Failed to fetch
```
→ Backend is not running (return to Step 1)

---

### **Step 5: Verify CORS Configuration**

**Backend should have:**
```python
# development/backend/fastapi_service/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "chrome-extension://*",  # ✅ Required
        "http://localhost:*",
        "http://127.0.0.1:*",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 🐛 Common Issues & Fixes

### **Issue 1: Backend Not Running**
**Symptom:** `Failed to fetch` error  
**Solution:**
```bash
cd development/backend
source ../../.venv/bin/activate
python fastapi_service/main.py
```

### **Issue 2: Extension Not Reloaded**
**Symptom:** Old code running, no new logs  
**Solution:**
- Go to `chrome://extensions/`
- Click 🔄 on Luminate AI extension
- Try query again

### **Issue 3: Port Conflict**
**Symptom:** Backend won't start, "port already in use"  
**Solution:**
```bash
# Find process using port 8000
lsof -ti:8000
# Kill it
kill -9 $(lsof -ti:8000)
# Restart backend
python fastapi_service/main.py
```

### **Issue 4: Wrong API Endpoint**
**Symptom:** 404 Not Found  
**Solution:**
- Verify endpoint: `/api/query` (not `/query`)
- Check `src/services/api.ts`:
```typescript
const API_BASE_URL = 'http://localhost:8000';
// ...
fetch(`${API_BASE_URL}/api/query`, ...)
```

### **Issue 5: Network/Firewall Blocking**
**Symptom:** Fetch fails, backend shows no requests  
**Solution:**
- Disable firewall temporarily
- Check antivirus settings
- Try `127.0.0.1:8000` instead of `localhost:8000`

---

## 🧪 Testing Checklist

Run through these tests after following steps:

- [ ] **Backend Health Check**
  ```bash
  curl http://localhost:8000/docs
  # Should return Swagger UI HTML
  ```

- [ ] **Direct API Test**
  ```bash
  curl -X POST http://localhost:8000/api/query \
    -H "Content-Type: application/json" \
    -d '{"query":"test"}'
  # Should return JSON response
  ```

- [ ] **Extension Loaded**
  - `chrome://extensions/` shows extension
  - Service worker is "active"
  - No errors in extension details

- [ ] **Console Logs Working**
  - Open DevTools on side panel
  - Send a message
  - See `🔵 Making unified query` log

- [ ] **Successful Query**
  - Send "explain gradient descent"
  - Response appears in chat
  - No red errors in console

---

## 📊 Debugging Output

### **Backend Logs (Terminal)**
```
INFO:     127.0.0.1:xxxxx - "POST /api/query HTTP/1.1" 200 OK
```

### **Extension Console (Chrome DevTools)**
```
🔵 Making unified query to: http://localhost:8000/api/query
✅ Unified query response: {
  mode: "educate",
  confidence: 0.85,
  reasoning: "...",
  response: {...}
}
```

### **Network Tab (Chrome DevTools)**
```
Request URL: http://localhost:8000/api/query
Request Method: POST
Status Code: 200 OK
```

---

## 🚀 Quick Fix Script

**Run this to reset everything:**

```bash
#!/bin/bash

# 1. Kill any existing backend
kill -9 $(lsof -ti:8000) 2>/dev/null

# 2. Rebuild extension
cd chrome-extension
npm run build

# 3. Start backend
cd ../development/backend
source ../../.venv/bin/activate
python fastapi_service/main.py &

# 4. Wait for backend
sleep 3

# 5. Test connection
curl -s http://localhost:8000/docs > /dev/null && echo "✅ Backend running" || echo "❌ Backend failed"

echo ""
echo "📝 Next steps:"
echo "1. Go to chrome://extensions/"
echo "2. Click 🔄 on Luminate AI"
echo "3. Open side panel and test"
```

---

## 📞 Still Having Issues?

### **Check Extension Errors**
1. `chrome://extensions/`
2. Click "Errors" on Luminate AI
3. Look for specific error messages

### **Check Backend Logs**
- Look in terminal running FastAPI
- Check for Python errors
- Verify imports loaded correctly

### **Verify ChromaDB**
```bash
cd /Users/aazain/Documents/GitHub/luminate-ai
ls chromadb_data/
# Should see .bin files
```

### **Check Environment**
```bash
source .venv/bin/activate
pip list | grep -E "fastapi|chromadb|google"
# Verify all packages installed
```

---

## ✅ Success Indicators

You'll know it's working when:

1. ✅ Backend terminal shows `POST /api/query` requests
2. ✅ Console shows `✅ Unified query response`
3. ✅ Messages appear in chat interface
4. ✅ No "Failed to fetch" errors
5. ✅ Math renders with KaTeX
6. ✅ Code highlights with Prism

---

## 🎯 Final Checklist

Before reporting issues, verify:

- [ ] Backend running (`python fastapi_service/main.py`)
- [ ] Extension built (`npm run build`)
- [ ] Extension reloaded in Chrome
- [ ] Port 8000 not blocked
- [ ] No firewall blocking localhost
- [ ] Chrome DevTools shows logs
- [ ] Network tab shows 200 OK responses

---

**If all else fails:** Restart Chrome completely, rebuild everything, and try again fresh.
