# Quick Start: Debugging Luminate AI Extension

## 🔄 First: Reload Extension

1. Go to `chrome://extensions/`
2. Find "Luminate AI Extension"
3. Click **reload button** (🔄)

## 📋 Then: Check Console

1. Visit: https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline
2. Press **F12** to open DevTools
3. Go to **Console** tab
4. Look for these logs:

### ✅ Expected Logs (Success)
```
[Luminate AI Loader] Initializing...
[Luminate AI Loader] Script injected, waiting for load...
[Luminate AI Loader] Content script loaded successfully
[Luminate AI] DOM already loaded, initializing now...
[Luminate AI] Container created, rendering React app...
[Luminate AI] React app rendered
[Luminate AI] Positioning button...
[Luminate AI] Initialization complete!
```

### ❌ If You See Errors

Copy **ALL** console output and share it with me!

## 🔍 Quick Checks

### Check 1: Is the root container created?
Run in console:
```javascript
document.getElementById('luminate-ai-root')
```
**Expected:** Should return `<div id="luminate-ai-root">...</div>`

### Check 2: Is the button element created?
Run in console:
```javascript
document.querySelector('.luminate-ai-button')
```
**Expected:** Should return `<button class="luminate-ai-button ...">...</button>`

### Check 3: Is the Help button found?
Run in console:
```javascript
document.querySelector('.ms-Button.ms-Button--icon.root-75')
```
**Expected:** Should return the Help button element

### Check 4: What's the button position?
Run in console:
```javascript
const btn = document.querySelector('.luminate-ai-button');
if (btn) {
  console.log({
    right: btn.style.right,
    bottom: getComputedStyle(btn).bottom,
    display: getComputedStyle(btn).display,
    zIndex: getComputedStyle(btn).zIndex
  });
} else {
  console.log('Button not found!');
}
```

## 📸 What to Share

Please share:
1. ✅ Screenshot of the **Console** tab (all logs)
2. ✅ Results from the 4 checks above
3. ✅ Screenshot of the page showing where button should be
4. ✅ Any red errors in console

## 🎯 Extension Files (Reference)

Location: `/Users/aazain/Documents/GitHub/luminate-ai/chrome-extension/dist`

Key files:
- `manifest.json` - Extension configuration
- `loader.js` - Runs in extension context, has chrome APIs
- `content.js` - Runs in page context, React app
- `content.css` - Button and chat styles

## 🚀 Button Should Appear

**Location:** Bottom right corner, to the left of the "Help" button
**Text:** "Luminate AI" with sparkle icon ✨
**Style:** Blue gradient, rounded, floating button

---

**Need Help?** Run the checks above and share the output!
