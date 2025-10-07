# Debugging the Luminate AI Extension

## Current Status
✅ Extension built with debugging logs
✅ Tests passing (6/6)
⏳ Testing button appearance on Blackboard

## Steps to Debug

### 1. Reload the Extension in Chrome

1. Go to `chrome://extensions/`
2. Find "Luminate AI Extension"
3. Click the **reload icon** (circular arrow)
4. This loads the new version with debug logs

### 2. Check Console Logs

1. Navigate to: `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
2. Open DevTools: **F12** or **Right-click → Inspect**
3. Go to the **Console** tab
4. Look for these logs:

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

### 3. What to Look For

#### ✅ Success Case
If you see all the logs above, the button should appear. If it doesn't:
- Check if `#luminate-ai-root` exists in the DOM
- Open Elements tab and search for `luminate-ai-button`

#### ❌ Error Cases

**Case 1: No logs at all**
- Extension not loaded properly
- URL doesn't match manifest patterns
- Check `chrome://extensions/` for errors

**Case 2: Loader logs but no content script logs**
```
[Luminate AI Loader] Initializing...
[Luminate AI Loader] Script injected, waiting for load...
❌ Failed to load content script: [error]
```
**Fix**: Content script file missing or not web-accessible

**Case 3: React/Module errors**
```
Uncaught SyntaxError: Cannot use import statement outside a module
```
**Fix**: Script type="module" not set correctly

**Case 4: Button created but not visible**
- Check CSS in Elements tab
- Look for `position: fixed` and `z-index` conflicts
- Blackboard might have higher z-index elements

### 4. Manual Inspection

Open the **Elements** tab in DevTools and search for:

1. **Container**: `#luminate-ai-root`
   - Should be at the end of `<body>`

2. **Button**: `.luminate-ai-button`
   - Should have classes: `fixed`, `bottom-5`, etc.
   - Check computed `right` position

3. **Help button**: `.ms-Button.ms-Button--icon.root-75`
   - This is the reference point for positioning

### 5. Test the Popup

1. Click the extension icon in Chrome toolbar
2. You should see "COMP237 Course Detected"
3. Click "Open Course Assistant"
4. Check console for:
```
[Luminate AI Loader] Received message: {action: "OPEN_CHAT"}
```

### 6. Common Issues & Fixes

#### Issue: Button not appearing

**Check 1: Is the page a Blackboard course page?**
```javascript
// Run in console
window.location.href
// Should contain: luminate.centennialcollege.ca/ultra/courses/
```

**Check 2: Is content script loaded?**
```javascript
// Run in console
document.getElementById('luminate-ai-root')
// Should return: <div id="luminate-ai-root">...</div>
```

**Check 3: React mount errors?**
```javascript
// Look for errors in console containing:
// "createRoot", "ReactDOM", "render"
```

**Check 4: CSS loaded?**
```javascript
// Run in console
[...document.styleSheets].find(s => s.href?.includes('content.css'))
// Should return a CSSStyleSheet object
```

#### Issue: Button appears but positioned wrong

**Check 5: Help button found?**
```javascript
// Run in console
document.querySelector('.ms-Button.ms-Button--icon.root-75')
// Should return the Help button element
```

**Check 6: Button position**
```javascript
// Run in console
const btn = document.querySelector('.luminate-ai-button');
console.log({
  right: btn.style.right,
  bottom: btn.style.bottom,
  zIndex: getComputedStyle(btn).zIndex
});
```

#### Issue: Chat not opening

**Check 7: State management**
- Click the Luminate AI button
- React should toggle `isChatOpen` state
- Check for React errors in console

**Check 8: ChatInterface component**
```javascript
// Check if chat container exists when open
document.querySelector('.luminate-ai-chat-container')
```

### 7. Force Initialization

If the button doesn't appear, try manually running the init in console:

```javascript
// This won't work directly due to module scope,
// but you can check if the script loaded:
console.log(window.location.href);
console.log(document.getElementById('luminate-ai-root'));
```

### 8. Network Errors

Check the **Network** tab for failed requests:
- `content.js` - Should load successfully (type: script)
- `utils.js` - React bundle
- `content.css` - Styles

All should return **200 OK** from `chrome-extension://`

## Expected Console Output

### Successful Load
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

### When Clicking Popup "Open Course Assistant"
```
[Luminate AI Loader] Received message: {action: "OPEN_CHAT"}
```

## Next Steps After Debugging

Once you see the logs, please share:
1. **All console output** (copy entire log)
2. **Any errors** (in red)
3. **Screenshot** of Elements tab showing `#luminate-ai-root`
4. **Whether the button appears** (even if positioned wrong)

This will help me fix the exact issue!
