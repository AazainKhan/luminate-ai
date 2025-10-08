# URL Support - Works on Any Luminate Page

**Updated:** October 7, 2025

---

## ✅ Extension Works On ALL Luminate Pages

The Luminate AI Chrome extension is **not limited to a specific course**. It works on **any page** under:

```
https://luminate.centennialcollege.ca/ultra/*
```

---

## Supported Pages

The extension activates and provides assistance on:

### Course Pages
- ✅ Course outline: `/ultra/courses/_XXXXX_1/outline`
- ✅ Course content: `/ultra/courses/_XXXXX_1/cl/outline`
- ✅ Announcements: `/ultra/courses/_XXXXX_1/announcements`
- ✅ Assignments: `/ultra/courses/_XXXXX_1/assignments`
- ✅ Grades: `/ultra/courses/_XXXXX_1/gradebook`
- ✅ Discussions: `/ultra/courses/_XXXXX_1/discussions`

### Platform Pages
- ✅ Calendar: `/ultra/calendar`
- ✅ Stream: `/ultra/stream`
- ✅ Activity stream
- ✅ Any other `/ultra/` page

---

## How It Works

### URL Pattern Matching

**Background Script** (`src/background/index.ts`):
```typescript
const BLACKBOARD_PATTERN = /^https:\/\/luminate\.centennialcollege\.ca\/ultra\//;
```

This regex matches:
- ✅ `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
- ✅ `https://luminate.centennialcollege.ca/ultra/courses/_11378_1/cl/outline`
- ✅ `https://luminate.centennialcollege.ca/ultra/calendar`
- ✅ `https://luminate.centennialcollege.ca/ultra/stream`
- ✅ Any page starting with `/ultra/`

### Manifest Permissions

**manifest.json**:
```json
{
  "host_permissions": [
    "https://luminate.centennialcollege.ca/*",
    "http://localhost:8000/*"
  ]
}
```

- Wildcard `*` allows access to all paths under the domain
- No course-specific restrictions

---

## Testing on Different Pages

### Test Case 1: Course Outline Page
```
URL: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline
Expected: ✅ Side panel available
Action: Click extension icon → opens AI assistant
```

### Test Case 2: Different Course
```
URL: https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline
Expected: ✅ Side panel available
Action: Same functionality on any course
```

### Test Case 3: Calendar
```
URL: https://luminate.centennialcollege.ca/ultra/calendar
Expected: ✅ Side panel available
Action: Can still access AI assistant for course help
```

### Test Case 4: Stream
```
URL: https://luminate.centennialcollege.ca/ultra/stream
Expected: ✅ Side panel available
Action: AI assistant accessible from activity stream
```

### Test Case 5: Non-Ultra Page (Should NOT work)
```
URL: https://luminate.centennialcollege.ca/login
Expected: ❌ Side panel NOT available
Reason: Not under /ultra/ path
```

---

## How to Use

1. **Install the Extension**
   - Load unpacked from `chrome-extension/dist/`
   - Extension appears in Chrome toolbar

2. **Navigate to ANY Luminate Page**
   - Go to `https://luminate.centennialcollege.ca/ultra/...`
   - Can be any course, calendar, stream, etc.

3. **Click Extension Icon**
   - Side panel opens automatically
   - Chat interface appears
   - Start asking questions

---

## Dynamic URL Detection

The extension automatically:

1. **Monitors URL changes** (`chrome.tabs.onUpdated`)
2. **Enables side panel** when URL matches `/ultra/`
3. **Disables side panel** when navigating away
4. **Persists across tabs** (each tab has independent state)

### Console Logs (for debugging)

When you navigate to a Luminate page, you'll see:
```
🔍 URL changed: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline
   Pattern match: true
✅ Side panel ENABLED for tab 123
```

When you leave a Luminate page:
```
🔍 URL changed: https://google.com
   Pattern match: false
🚪 Side panel DISABLED (not on /ultra/)
```

---

## Course-Specific Features

Even though the extension works on **any** page, certain features may be **course-aware**:

### Backend Intelligence
- Retrieves content from current course (if on course page)
- Adapts responses based on course context
- Tracks student progress per course

### URL Parsing
The backend can extract course ID from URL:
```
URL: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline
Extracted: course_id = "_29430_1"
```

This allows:
- Course-specific content retrieval
- Personalized recommendations per course
- Multi-course support (student taking multiple courses)

---

## Future Enhancements

### Potential URL-Aware Features

1. **Course Auto-Detection**
   - Parse course ID from URL
   - Load course-specific knowledge base
   - Show course name in side panel header

2. **Page-Specific Context**
   - On assignment page → suggest assignment help
   - On grades page → show study recommendations
   - On calendar → show upcoming deadlines

3. **Multi-Course Support**
   - Student enrolled in COMP237, MATH123, etc.
   - Extension works in all courses
   - Backend maintains separate context per course

---

## Configuration Files Updated

### ✅ Files Changed
1. **`scripts/validate-build.js`**
   - Updated instruction: "Navigate to any Luminate page: https://luminate.centennialcollege.ca/ultra/..."
   - Removed course-specific URL reference

2. **`src/popup/Popup.tsx`**
   - Updated message: "Navigate to any Luminate Blackboard page to use Luminate AI"
   - Clarified not limited to COMP237

3. **`docs/README.md`**
   - Documented: "Works on: course pages, calendar, stream, grades, announcements, etc."
   - Added examples for different page types

### ✅ Already Correct
- **`manifest.json`**: Host permissions already use wildcard `*`
- **`src/background/index.ts`**: Regex already matches all `/ultra/` pages
- No course-specific hardcoding in core logic

---

## Summary

**Key Points:**
- ✅ Extension works on **any** `luminate.centennialcollege.ca/ultra/*` page
- ✅ Not limited to specific courses (COMP237, etc.)
- ✅ URL pattern is generic: `/ultra/` path detection
- ✅ Dynamically enables/disables based on current URL
- ✅ Backend can extract course context from URL when needed

**User Experience:**
- Install once → works everywhere on Luminate
- No reconfiguration needed for different courses
- Side panel available across all /ultra/ pages
- Seamless multi-course support

**Technical Implementation:**
- Regex: `/^https:\/\/luminate\.centennialcollege\.ca\/ultra\//`
- Permissions: `"https://luminate.centennialcollege.ca/*"`
- Dynamic tab monitoring with `chrome.tabs.onUpdated`
- Per-tab side panel state management

---

**Ready to use on any Luminate Blackboard page!** 🎓✨
