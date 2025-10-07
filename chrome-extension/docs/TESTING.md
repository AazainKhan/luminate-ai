# Chrome Extension Testing Guide

## Test Plan for Luminate AI Side Panel Extension

### Prerequisites
- Chrome browser installed
- Extension built (`npm run build`)
- Backend running on `http://localhost:8000`

---

## Test Suite 1: Installation & Loading

### Test 1.1: Load Extension
**Steps:**
1. Open Chrome
2. Navigate to `chrome://extensions/`
3. Enable "Developer mode" (top right toggle)
4. Click "Load unpacked"
5. Select: `/Users/aazain/Documents/GitHub/luminate-ai/chrome-extension/dist`

**Expected:**
- ✅ Extension loads without errors
- ✅ "Luminate AI - COMP237 Course Assistant" appears in extension list
- ✅ Extension icon visible in toolbar

**Actual:** _____________________

---

### Test 1.2: Verify Permissions
**Steps:**
1. Click "Details" on the extension card
2. Review permissions

**Expected:**
- ✅ Storage permission granted
- ✅ Access to `luminate.centennialcollege.ca`
- ✅ Access to `localhost:8000`
- ✅ Side panel permission granted

**Actual:** _____________________

---

## Test Suite 2: Side Panel Behavior

### Test 2.1: Open Side Panel on Blackboard
**Steps:**
1. Navigate to: `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
2. Click the Luminate AI extension icon in toolbar

**Expected:**
- ✅ Side panel opens on the right side of browser
- ✅ ChatInterface loads with Luminate AI branding
- ✅ Input field is visible and functional
- ✅ No console errors in DevTools

**Actual:** _____________________

---

### Test 2.2: Side Panel Disabled on Non-Blackboard Sites
**Steps:**
1. Navigate to: `https://google.com`
2. Try clicking the Luminate AI extension icon

**Expected:**
- ✅ Extension icon appears disabled/grayed out
- ✅ Side panel does NOT open
- ✅ Console shows: "⚠️ Side panel only works on Blackboard pages"

**Actual:** _____________________

---

### Test 2.3: Side Panel Auto-Disable on Navigation Away
**Steps:**
1. Navigate to Blackboard: `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
2. Open side panel (click extension icon)
3. Navigate away to: `https://google.com`

**Expected:**
- ✅ Side panel automatically closes
- ✅ Console shows: "🚪 Side panel disabled - left Blackboard"
- ✅ Extension icon becomes disabled

**Actual:** _____________________

---

### Test 2.4: Side Panel Re-Enable on Return to Blackboard
**Steps:**
1. Start on `https://google.com`
2. Navigate back to: `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`

**Expected:**
- ✅ Extension icon becomes enabled
- ✅ Console shows: "✅ Side panel enabled - on Blackboard"
- ✅ Can click icon to open side panel

**Actual:** _____________________

---

### Test 2.5: Tab Switching Behavior
**Steps:**
1. Tab 1: Open Blackboard course page
2. Tab 2: Open `https://google.com`
3. Open side panel in Tab 1
4. Switch to Tab 2
5. Switch back to Tab 1

**Expected:**
- ✅ Side panel stays open in Tab 1
- ✅ Extension disabled in Tab 2
- ✅ Side panel persists when returning to Tab 1

**Actual:** _____________________

---

## Test Suite 3: Chat Functionality

### Test 3.1: Send Basic Query
**Steps:**
1. Open side panel on Blackboard
2. Type: "What is supervised learning?"
3. Click send button (or press Enter)

**Expected:**
- ✅ Loading spinner appears
- ✅ Response appears within 10 seconds
- ✅ Response contains AI-generated explanation
- ✅ No error messages

**Actual:** _____________________

---

### Test 3.2: View Content Results
**Steps:**
1. Send query: "Tell me about neural networks"
2. Wait for response

**Expected:**
- ✅ "Related Course Content" section appears
- ✅ Content cards show:
  - Module name
  - Content title
  - Relevance explanation
  - Clickable link
- ✅ Links are functional (open in new tab)

**Actual:** _____________________

---

### Test 3.3: Related Topics
**Steps:**
1. Send query: "What is machine learning?"
2. Wait for response
3. Observe "Related Topics" section

**Expected:**
- ✅ Related topics appear as clickable pills
- ✅ Hovering shows "why_explore" tooltip
- ✅ Clicking a topic fills input field with topic title
- ✅ Can send related topic as new query

**Actual:** _____________________

---

### Test 3.4: Next Steps
**Steps:**
1. Send query with actionable response
2. Check for "Next Steps" section

**Expected:**
- ✅ Next steps appear if provided by backend
- ✅ Steps are numbered/listed clearly
- ✅ Text is readable and helpful

**Actual:** _____________________

---

### Test 3.5: Message History
**Steps:**
1. Send query: "What is AI?"
2. Send query: "What is machine learning?"
3. Send query: "What is deep learning?"
4. Scroll up in chat

**Expected:**
- ✅ All 3 queries and responses are visible
- ✅ Scroll works smoothly
- ✅ Message order is correct (oldest at top)
- ✅ No messages are lost

**Actual:** _____________________

---

## Test Suite 4: Error Handling

### Test 4.1: Backend Offline
**Steps:**
1. Stop backend server (`Ctrl+C` in terminal)
2. Send query: "What is AI?"

**Expected:**
- ✅ Error message appears
- ✅ Message states backend connection failed
- ✅ UI remains functional (can try again)

**Actual:** _____________________

---

### Test 4.2: Empty Query
**Steps:**
1. Click send button without typing anything
2. Type only spaces, then send

**Expected:**
- ✅ Nothing happens (no API call)
- ✅ Input field remains focused
- ✅ No error message

**Actual:** _____________________

---

### Test 4.3: Very Long Query
**Steps:**
1. Type a 500+ character query
2. Send query

**Expected:**
- ✅ Query is accepted
- ✅ Backend processes successfully
- ✅ Response appears normally

**Actual:** _____________________

---

## Test Suite 5: UI/UX

### Test 5.1: Responsive Layout
**Steps:**
1. Open side panel
2. Resize Chrome window to different widths

**Expected:**
- ✅ Side panel adapts to window size
- ✅ Text wraps properly
- ✅ No horizontal scrolling needed
- ✅ All elements remain visible

**Actual:** _____________________

---

### Test 5.2: Scrolling
**Steps:**
1. Send multiple queries to fill chat
2. Test scrolling behavior

**Expected:**
- ✅ Auto-scrolls to newest message
- ✅ Can scroll up to see history
- ✅ Scroll is smooth
- ✅ Input field stays at bottom

**Actual:** _____________________

---

### Test 5.3: Loading States
**Steps:**
1. Send query and observe loading states

**Expected:**
- ✅ Loading spinner appears immediately
- ✅ Send button disabled during loading
- ✅ Input field disabled during loading
- ✅ Loading clears when response arrives

**Actual:** _____________________

---

## Test Suite 6: Performance

### Test 6.1: Initial Load Time
**Steps:**
1. Click extension icon on Blackboard
2. Measure time to fully loaded UI

**Expected:**
- ✅ Side panel opens in < 1 second
- ✅ UI is immediately interactive
- ✅ No lag or freezing

**Actual:** _____________________

---

### Test 6.2: Query Response Time
**Steps:**
1. Send query: "What is supervised learning?"
2. Measure time to response

**Expected:**
- ✅ Response arrives in < 10 seconds
- ✅ Loading indicator shows progress
- ✅ No timeout errors

**Actual:** _____________________

---

### Test 6.3: Multiple Rapid Queries
**Steps:**
1. Send 5 queries in rapid succession (before responses arrive)

**Expected:**
- ✅ All queries are queued
- ✅ Responses arrive in order
- ✅ No race conditions or dropped messages
- ✅ UI remains responsive

**Actual:** _____________________

---

## Test Suite 7: Edge Cases

### Test 7.1: Refresh During Query
**Steps:**
1. Send query
2. Immediately refresh page (F5)

**Expected:**
- ✅ Extension reloads cleanly
- ✅ Side panel closes
- ✅ Can reopen and use normally
- ✅ No console errors

**Actual:** _____________________

---

### Test 7.2: Multiple Windows
**Steps:**
1. Open 2 Chrome windows
2. Both on Blackboard pages
3. Open side panel in both

**Expected:**
- ✅ Side panels work independently
- ✅ Each maintains own chat history
- ✅ No cross-contamination of messages

**Actual:** _____________________

---

### Test 7.3: Special Characters in Query
**Steps:**
1. Send query with emojis: "What is AI? 🤖"
2. Send query with symbols: "What is A&B | C?"

**Expected:**
- ✅ Special characters handled correctly
- ✅ Backend processes query
- ✅ Response appears normally

**Actual:** _____________________

---

## Test Suite 8: Console Logs

### Test 8.1: Background Worker Logs
**Steps:**
1. Open `chrome://extensions/`
2. Click "Service worker" link under extension
3. Navigate around Blackboard

**Expected Console Logs:**
```
✨ Luminate AI extension installed
✅ Side panel enabled - on Blackboard
🚪 Side panel disabled - left Blackboard
```

**Actual:** _____________________

---

### Test 8.2: No Errors in Production
**Steps:**
1. Open DevTools on side panel
2. Use extension normally for 5 minutes

**Expected:**
- ✅ No red errors in console
- ✅ No uncaught exceptions
- ✅ Only info/log messages (optional)

**Actual:** _____________________

---

## Summary

**Total Tests:** 28
**Passed:** _____
**Failed:** _____
**Blocked:** _____

### Critical Issues Found:
1. _____________________
2. _____________________
3. _____________________

### Minor Issues Found:
1. _____________________
2. _____________________

### Notes:
_____________________
_____________________
_____________________

---

## Regression Testing Checklist

Before each release, verify:
- [ ] All Test Suite 1 tests pass (Installation)
- [ ] All Test Suite 2 tests pass (Side Panel Behavior)
- [ ] All Test Suite 3 tests pass (Chat Functionality)
- [ ] At least 80% of other tests pass
- [ ] No critical console errors
- [ ] Backend integration works end-to-end
