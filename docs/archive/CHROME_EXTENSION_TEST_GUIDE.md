# Chrome Extension Manual Testing Guide

## ✅ Pre-Test Checklist

**Backend Status:**
- ✅ Backend running on http://localhost:8000
- ✅ ChromaDB loaded: 917 documents
- ✅ Math Translation Agent: 15 formulas available
- ✅ RAG retrieval: Working for conceptual queries
- ✅ All automated tests: Passing (100%)

**Extension Build:**
- ✅ Built: 515 KB `sidepanel.js`
- ✅ Location: `/chrome-extension/dist`

---

## 📋 Setup Instructions

### 1. Load Extension in Chrome

```
1. Open Chrome browser
2. Navigate to: chrome://extensions/
3. Enable "Developer mode" (toggle top-right)
4. Click "Load unpacked"
5. Select folder: /Users/aazain/Documents/GitHub/luminate-ai/chrome-extension/dist
6. Verify extension icon appears in toolbar
7. Click extension icon to open sidepanel
```

---

## 🧪 Test Cases

### Test Suite 1: Conceptual Queries (NEW - RAG Integration)

**Purpose:** Validate ChromaDB RAG retrieval for conceptual topics

#### Test 1.1: Intelligent Agents
```
Query: "Explain Week 2 intelligent agents simply"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Returns course content (not mock message)
- ✅ Shows structured sections:
  - 📖 Summary
  - 🔍 Key Details
  - 📑 Sources
- ✅ Cites sources at bottom (Topics 2.1, 2.3)
- ✅ No "I'm currently in mock mode" message

**What to Look For:**
- Content mentions: "rational intelligent agents", "agent function", "PEAS"
- Sources list module/topic names
- Markdown formatting renders correctly

---

#### Test 1.2: Search Algorithms
```
Query: "what are search algorithms"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Returns Module 4 content
- ✅ Mentions: A* search, informed search, uninformed search
- ✅ Sources cite Module 4 topics
- ✅ Structured explanation with sections

---

#### Test 1.3: Heuristic Functions
```
Query: "explain heuristic functions"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Returns Topics 4.1, 4.4 content
- ✅ Explains admissibility, consistency
- ✅ Sources properly cited
- ✅ Tip at bottom suggests formula queries

---

### Test Suite 2: Math Translation Agent (Original Formulas)

**Purpose:** Validate 4-level formula explanations with LaTeX and code

#### Test 2.1: Gradient Descent
```
Query: "explain gradient descent"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Shows 4-level structure:
  - 🎯 Level 1: Intuition (5-year-old explanation)
  - 📐 Level 2: Math Translation (LaTeX formulas)
  - 💻 Level 3: Code Example (Python with syntax highlighting)
  - ⚠️ Level 4: Common Misconceptions
- ✅ LaTeX renders with KaTeX (θ, ∇, α symbols visible)
- ✅ Python code syntax highlighted
- ✅ Misconceptions clearly marked (❌ wrong → ✅ right)

**What to Look For:**
- Formula: θ_{new} = θ_{old} - α∇J(θ)
- Code includes gradient calculation and weight update
- Misconceptions about learning rate, local minima

---

#### Test 2.2: Backpropagation
```
Query: "what is backpropagation"
Mode: Educate Mode
```

**Expected Results:**
- ✅ 4-level structure complete
- ✅ Chain rule formula in LaTeX
- ✅ Python code for forward/backward pass
- ✅ Misconceptions about vanishing gradients

---

#### Test 2.3: Sigmoid Activation
```
Query: "sigmoid activation function"
Mode: Educate Mode
```

**Expected Results:**
- ✅ 4-level structure complete
- ✅ Formula: σ(x) = 1/(1 + e^(-x))
- ✅ Code for sigmoid and derivative
- ✅ Misconceptions about output range

---

### Test Suite 3: New Formulas (Recently Added)

**Purpose:** Validate new formula additions

#### Test 3.1: Mean Squared Error
```
Query: "what is MSE"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Formula name: "Mean Squared Error (MSE)"
- ✅ 4 levels present
- ✅ LaTeX formula visible
- ✅ Python implementation included

---

#### Test 3.2: Dropout
```
Query: "explain dropout"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Formula name: "Dropout"
- ✅ Explains regularization technique
- ✅ Python code with mask generation
- ✅ Misconceptions about training vs inference

---

#### Test 3.3: Adam Optimizer
```
Query: "adam optimizer"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Formula name: "Adam Optimizer"
- ✅ Explains momentum + RMSprop combination
- ✅ Beta parameters explained
- ✅ Code implementation present

---

#### Test 3.4: Batch Normalization
```
Query: "batch normalization"
Mode: Educate Mode
```

**Expected Results:**
- ✅ Formula name: "Batch Normalization"
- ✅ Formula with mean/variance normalization
- ✅ Code for training and inference modes
- ✅ Misconceptions about when to use

---

### Test Suite 4: Navigate Mode

**Purpose:** Validate ChromaDB search and resource card display

#### Test 4.1: Module Navigation
```
Query: "find week 3 slides"
Mode: Navigate Mode
```

**Expected Results:**
- ✅ ChromaDB search executes
- ✅ Results displayed as resource cards
- ✅ Each card shows:
  - Document title
  - Module name
  - Content preview
  - Blackboard URL (if available)
- ✅ URLs are clickable

---

#### Test 4.2: Topic Search
```
Query: "show me search algorithms resources"
Mode: Navigate Mode
```

**Expected Results:**
- ✅ Returns Module 4 materials
- ✅ Resource cards for topics 4.1-4.4
- ✅ Preview text visible

---

### Test Suite 5: Mode Switching

**Purpose:** Validate mode indicator and seamless switching

#### Test 5.1: Switch Educate → Navigate
```
1. Start in Educate Mode
2. Query: "explain gradient descent" (educate)
3. Switch to Navigate Mode
4. Query: "find gradient descent examples" (navigate)
```

**Expected Results:**
- ✅ Mode indicator updates correctly
- ✅ Different response formats
- ✅ No errors during switch

---

#### Test 5.2: Switch Navigate → Educate
```
1. Start in Navigate Mode
2. Query: "find week 2 materials" (navigate)
3. Switch to Educate Mode
4. Query: "explain intelligent agents" (educate)
```

**Expected Results:**
- ✅ Mode changes reflected in UI
- ✅ Appropriate response format
- ✅ Smooth transition

---

## 🐛 Known Issues to Verify

### Issue 1: Orchestrator Routing (Minor)
**Problem:** Some "what is X" queries route to Navigate instead of Educate

**Test Cases:**
```
Query: "what is softmax"
Current: Routes to Navigate mode ❌
Expected: Should route to Educate mode ✅

Query: "what is F1 score"
Current: Routes to Navigate mode ❌
Expected: Should route to Educate mode ✅
```

**Workaround:** Use "explain softmax" or "softmax function" instead

**Severity:** Low (works with different phrasing)

---

### Issue 2: Learning Rate Formula Matching
**Problem:** "learning rate decay" matches Gradient Descent instead

**Test Case:**
```
Query: "learning rate decay"
Current: Returns Gradient Descent formula ❌
Expected: Should return Learning Rate Scheduling ✅
```

**Workaround:** Use "learning rate scheduling" instead

**Severity:** Low (works with specific phrasing)

---

## ✅ Success Criteria

**For Test to Pass:**
1. ✅ All conceptual queries return course content (no mock message)
2. ✅ All math queries return 4-level structure
3. ✅ LaTeX formulas render correctly
4. ✅ Python code has syntax highlighting
5. ✅ Navigate mode shows resource cards
6. ✅ Mode switching works smoothly
7. ✅ No console errors in Chrome DevTools
8. ✅ Backend API calls succeed (check Network tab)

---

## 📊 Results Template

**After Testing, Record:**

```
Test Suite 1: Conceptual Queries (RAG Integration)
  Test 1.1: Intelligent Agents - [ ] PASS / [ ] FAIL
  Test 1.2: Search Algorithms - [ ] PASS / [ ] FAIL
  Test 1.3: Heuristic Functions - [ ] PASS / [ ] FAIL

Test Suite 2: Math Translation Agent (Original)
  Test 2.1: Gradient Descent - [ ] PASS / [ ] FAIL
  Test 2.2: Backpropagation - [ ] PASS / [ ] FAIL
  Test 2.3: Sigmoid - [ ] PASS / [ ] FAIL

Test Suite 3: New Formulas
  Test 3.1: MSE - [ ] PASS / [ ] FAIL
  Test 3.2: Dropout - [ ] PASS / [ ] FAIL
  Test 3.3: Adam - [ ] PASS / [ ] FAIL
  Test 3.4: Batch Norm - [ ] PASS / [ ] FAIL

Test Suite 4: Navigate Mode
  Test 4.1: Module Navigation - [ ] PASS / [ ] FAIL
  Test 4.2: Topic Search - [ ] PASS / [ ] FAIL

Test Suite 5: Mode Switching
  Test 5.1: Educate → Navigate - [ ] PASS / [ ] FAIL
  Test 5.2: Navigate → Educate - [ ] PASS / [ ] FAIL
```

---

## 🔧 Troubleshooting

**If conceptual queries show mock message:**
- Check backend logs for RAG retrieval errors
- Verify ChromaDB has 917 documents loaded
- Test query via curl: `curl -X POST http://localhost:8000/api/query -d '{"query":"explain intelligent agents"}'`

**If math formulas don't render:**
- Check browser console for KaTeX errors
- Verify LaTeX delimiters ($, $$) present in response
- Check KaTeX library loaded in extension

**If extension doesn't load:**
- Check Chrome console for build errors
- Verify dist folder has all files (manifest.json, sidepanel.js, sidepanel.html)
- Try rebuilding: `cd chrome-extension && npm run build`

**If backend not responding:**
- Check: `curl http://localhost:8000/health`
- Restart: `lsof -ti:8000 | xargs kill -9 && cd development/backend && source ../../.venv/bin/activate && python fastapi_service/main.py`

---

## 📝 Next Steps After Testing

**If All Tests Pass:**
1. ✅ Mark "Manual Chrome extension testing" as completed
2. 🎨 Start visual diagram generation (matplotlib integration)
3. 📚 Expand formula library to 30+ formulas
4. 🔧 Fix orchestrator routing for "what is X" queries

**If Tests Fail:**
1. 🐛 Document failures in detail
2. 🔍 Check Chrome DevTools console
3. 🔍 Check Network tab for API errors
4. 🔍 Review backend logs
5. 🛠️ Fix issues and re-test

---

## 🎯 Testing Priority

**High Priority (Must Work):**
- ✅ Conceptual queries retrieve course content
- ✅ Math formulas show 4-level structure
- ✅ LaTeX renders correctly
- ✅ Code syntax highlighting works

**Medium Priority (Should Work):**
- ✅ Navigate mode shows resources
- ✅ Mode switching smooth
- ✅ Sources properly cited

**Low Priority (Nice to Have):**
- ✅ All new formulas accessible
- ✅ Workarounds for routing issues documented

---

## 📅 Testing Timeline

**Estimated Time:** 30-45 minutes

**Breakdown:**
- Setup (5 min): Load extension in Chrome
- Test Suite 1 (10 min): Conceptual queries
- Test Suite 2 (10 min): Original formulas
- Test Suite 3 (10 min): New formulas
- Test Suite 4 (5 min): Navigate mode
- Test Suite 5 (5 min): Mode switching
- Documentation (5 min): Record results

---

**Ready to Test!** 🚀

Backend is healthy, extension is built, all automated tests passing. Just need manual validation in Chrome browser.
