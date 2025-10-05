# URL Pattern Testing Guide

## Pattern Being Tested
```regex
/^https:\/\/luminate\.centennialcollege\.ca\/ultra\//
```

This means the side panel will be **enabled** on ANY URL that starts with:
```
https://luminate.centennialcollege.ca/ultra/
```

---

## ✅ URLs That SHOULD Work (Side Panel Enabled)

### Courses
- `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
- `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/cl/outline`
- `https://luminate.centennialcollege.ca/ultra/courses/ANY_COURSE_ID/ANY_PAGE`

### Calendar
- `https://luminate.centennialcollege.ca/ultra/calendar`

### Stream/Dashboard
- `https://luminate.centennialcollege.ca/ultra/stream`
- `https://luminate.centennialcollege.ca/ultra/`

### Any Other /ultra/ Page
- `https://luminate.centennialcollege.ca/ultra/grades`
- `https://luminate.centennialcollege.ca/ultra/institution-page`
- Basically ANYTHING under `/ultra/`

---

## ❌ URLs That Should NOT Work (Side Panel Disabled)

### Old Blackboard Interface
- `https://luminate.centennialcollege.ca/webapps/portal/execute/tabs/tabAction`
- `https://luminate.centennialcollege.ca/webapps/blackboard/content/listContent.jsp`

### Login Page
- `https://luminate.centennialcollege.ca/`

### Non-Blackboard Sites
- `https://google.com`
- `https://github.com`
- Any other website

---

## 🧪 Test Procedure

### 1. Reload Extension
```
chrome://extensions/ → Click reload (🔄)
```

### 2. Open Service Worker Console
```
chrome://extensions/ → Click "Service worker" link
```

### 3. Test Valid URLs
Navigate to each URL below and verify:

**Test A: Course Outline**
- URL: `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
- **Expected logs:**
  ```
  🔍 URL changed: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline
     Pattern match: true
  ✅ Side panel ENABLED for tab [ID]
  ```
- **Extension icon:** Should be COLORED/ACTIVE
- **Click icon:** Side panel should OPEN

**Test B: Stream/Dashboard**
- URL: `https://luminate.centennialcollege.ca/ultra/stream`
- **Expected logs:**
  ```
  🔍 URL changed: https://luminate.centennialcollege.ca/ultra/stream
     Pattern match: true
  ✅ Side panel ENABLED for tab [ID]
  ```
- **Extension icon:** Should be COLORED/ACTIVE
- **Click icon:** Side panel should OPEN

**Test C: Calendar**
- URL: `https://luminate.centennialcollege.ca/ultra/calendar`
- **Expected logs:**
  ```
  🔍 URL changed: https://luminate.centennialcollege.ca/ultra/calendar
     Pattern match: true
  ✅ Side panel ENABLED for tab [ID]
  ```
- **Extension icon:** Should be COLORED/ACTIVE
- **Click icon:** Side panel should OPEN

### 4. Test Invalid URLs

**Test D: Non-Ultra Blackboard Page**
- URL: `https://luminate.centennialcollege.ca/webapps/portal/execute/tabs/tabAction`
- **Expected logs:**
  ```
  🔍 URL changed: https://luminate.centennialcollege.ca/webapps/...
     Pattern match: false
  🚪 Side panel DISABLED (not on /ultra/)
  ```
- **Extension icon:** Should be GRAYED OUT/DISABLED
- **Click icon:** Nothing should happen

**Test E: External Site**
- URL: `https://google.com`
- **Expected logs:**
  ```
  🔍 URL changed: https://google.com
     Pattern match: false
  🚪 Side panel DISABLED (not on /ultra/)
  ```
- **Extension icon:** Should be GRAYED OUT/DISABLED
- **Click icon:** Nothing should happen

### 5. Test Tab Switching

**Setup:**
1. Open Tab 1: `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
2. Open Tab 2: `https://google.com`

**Test:**
- Switch to Tab 1 → Icon should be COLORED
- Switch to Tab 2 → Icon should be GRAYED OUT
- Switch back to Tab 1 → Icon should be COLORED again

**Expected logs when switching:**
```
🔄 Tab activated: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline
   Pattern match: true
✅ Side panel ENABLED for tab [ID]
```

---

## 📊 Test Results Template

```
✅ / ❌  Test A: Course Outline - Side panel enabled
✅ / ❌  Test B: Stream/Dashboard - Side panel enabled  
✅ / ❌  Test C: Calendar - Side panel enabled
✅ / ❌  Test D: Non-Ultra Blackboard - Side panel disabled
✅ / ❌  Test E: External Site - Side panel disabled
✅ / ❌  Test F: Tab Switching - Correctly enables/disables

Notes:
_________________________________________________________________
_________________________________________________________________
_________________________________________________________________
```

---

## 🐛 If Tests Fail

### Pattern Not Matching (false when should be true)
**Check in Service Worker console:**
```javascript
// Test the pattern manually
const pattern = /^https:\/\/luminate\.centennialcollege\.ca\/ultra\//;
const testURL = 'https://luminate.centennialcollege.ca/ultra/stream';
console.log('Match:', pattern.test(testURL));
```

### Side Panel Not Opening
1. Check if icon is colored (side panel enabled)
2. Look for errors in Service Worker console
3. Check side panel DevTools for loading errors

### Logs Not Appearing
- Service worker might have stopped
- Click "Service worker" link again to wake it up
- Try reloading the extension

---

## ✅ Success Criteria

All of these should be true:
- [ ] Side panel enabled on ALL `/ultra/` URLs
- [ ] Side panel disabled on non-`/ultra/` URLs
- [ ] Tab switching updates icon state correctly
- [ ] Console logs show pattern matching correctly
- [ ] Clicking icon opens side panel when enabled
- [ ] Side panel loads with Luminate AI UI (not blank)
