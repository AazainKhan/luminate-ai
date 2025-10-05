# Debug Checklist - Side Panel Not Opening

## 🔍 Step-by-Step Debugging

### Step 1: Reload Extension
1. Go to `chrome://extensions/`
2. Find "Luminate AI - COMP237 Course Assistant"
3. Click the **reload button (🔄)**
4. ✅ Confirm: Extension status shows "Errors" button is **NOT** visible

---

### Step 2: Check Service Worker Console
1. On `chrome://extensions/` page
2. Under "Luminate AI" extension, click **"Service worker"** (blue link)
3. A DevTools window should open

**Expected logs immediately:**
```
✨ Side panel behavior initialized
✨ Luminate AI extension installed (if first install)
```

**If you see errors here, copy and report them!**

---

### Step 3: Navigate to Blackboard
1. Open a new tab
2. Navigate to: `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
3. Wait for page to fully load

**Check Service Worker console for:**
```
✅ Side panel enabled - on Blackboard: https://luminate.centennialcollege.ca/ultra/...
```

**If you don't see this log, the URL monitoring isn't working!**

---

### Step 4: Check Extension Icon
1. Look at the Luminate AI icon in Chrome toolbar
2. Is it **grayed out** or **colored**?
   - **Colored** = Side panel enabled ✅
   - **Grayed out** = Side panel disabled ❌

**If grayed out on Blackboard page:**
- Something is wrong with URL pattern matching
- Report the exact URL you're on

---

### Step 5: Click Extension Icon
1. Click the Luminate AI icon in toolbar
2. What happens?

**Possible outcomes:**
- ✅ **Side panel opens** → Success!
- ❌ **Nothing happens** → Check for errors in Service Worker console
- ❌ **Error popup** → Copy the error message

---

### Step 6: Check for Errors
Open the Service Worker console and look for:
- 🔴 **Red error messages**
- ⚠️ **Yellow warnings**
- Any messages containing "side panel", "gesture", or "enabled"

**Common errors and fixes:**

| Error | Fix |
|-------|-----|
| "No active side panel for tabId" | Side panel not enabled for this tab |
| "sidePanel.open() may only be called in response to a user gesture" | Already fixed with setPanelBehavior |
| "Cannot read properties of undefined (reading 'setPanelBehavior')" | Chrome doesn't support this API |

---

## 🧪 Advanced Debugging

### Check Chrome Version
1. Go to `chrome://version/`
2. Look for "Google Chrome" version

**Required:** Chrome 114+ (Side Panel API introduced in Chrome 114)

**If older version:** Update Chrome to latest version

---

### Manual Enable Test
Try manually enabling in Service Worker console:

```javascript
// Copy and paste into Service Worker console:
chrome.sidePanel.setPanelBehavior({ openPanelOnActionClick: true })
  .then(() => console.log('✅ Behavior set'))
  .catch(err => console.error('❌ Error:', err));

// Then get current tab and enable:
chrome.tabs.query({ active: true, currentWindow: true }, (tabs) => {
  const tabId = tabs[0].id;
  chrome.sidePanel.setOptions({ tabId, enabled: true })
    .then(() => console.log('✅ Enabled for tab', tabId))
    .catch(err => console.error('❌ Error:', err));
});
```

**If this works but icon click doesn't:**
- The initialization is failing
- Report the console output

---

### Check Manifest Permissions
1. Click "Details" on extension in `chrome://extensions/`
2. Scroll to "Permissions"

**Should see:**
- ✅ "Read and change data on luminate.centennialcollege.ca"
- ✅ "Use the side panel"

**If missing:** Manifest issue - report this

---

## 📋 Report Template

If still not working, please provide:

```
**Chrome Version:** [Get from chrome://version/]

**Extension Loaded:** ✅ / ❌

**Current URL:** [The Blackboard URL you're on]

**Extension Icon State:** Colored / Grayed Out

**Service Worker Console Logs:**
[Paste all logs here]

**Service Worker Console Errors:**
[Paste any red errors here]

**What happens when you click icon:**
[Describe what you see]

**Manual enable test result:**
[Paste console output from Advanced Debugging section]
```

---

## 🎯 Quick Test Commands

**Run in Service Worker console to debug:**

```javascript
// 1. Check if side panel API exists
console.log('Side Panel API available:', typeof chrome.sidePanel !== 'undefined');

// 2. Check current behavior
chrome.sidePanel.getPanelBehavior()
  .then(behavior => console.log('Current behavior:', behavior))
  .catch(err => console.error('Error getting behavior:', err));

// 3. List all tabs
chrome.tabs.query({}, tabs => {
  console.log('All tabs:', tabs.map(t => ({ id: t.id, url: t.url })));
});

// 4. Force enable for active tab
chrome.tabs.query({ active: true, currentWindow: true }, async (tabs) => {
  if (tabs[0]) {
    try {
      await chrome.sidePanel.setOptions({ tabId: tabs[0].id, enabled: true });
      console.log('✅ Force enabled for tab', tabs[0].id);
    } catch (err) {
      console.error('❌ Force enable failed:', err);
    }
  }
});
```

---

## 💡 Most Common Issues

1. **Not reloading extension after rebuild**
   - Fix: Click reload button on chrome://extensions/

2. **Wrong URL pattern**
   - Must be: `https://luminate.centennialcollege.ca/ultra/...`
   - Won't work on: `https://luminate.centennialcollege.ca/webapps/...`

3. **Chrome version too old**
   - Fix: Update to Chrome 114+

4. **Service worker not running**
   - Fix: Click "Service worker" link to wake it up

5. **Extension icon not visible in toolbar**
   - Fix: Click puzzle piece icon → Pin "Luminate AI"
