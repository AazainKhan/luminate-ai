# Shadcn MCP Setup for Chrome Extension

## ✅ What's Done

1. Created `.vscode/mcp.json` with shadcn MCP server configuration
2. Updated background worker to attempt auto-close when navigating away

---

## 🔧 Next Steps: Enable Shadcn MCP in VS Code

### Step 1: Open MCP Configuration
- Press `Cmd+Shift+P` (Mac) or `Ctrl+Shift+P` (Windows/Linux)
- Type: `MCP: Open User Configuration`
- Or use the workspace config we created: `.vscode/mcp.json`

### Step 2: Enable Agent Mode
1. Open GitHub Copilot Chat (`Ctrl+Cmd+I` on Mac, `Ctrl+Alt+I` on Windows/Linux)
2. Select **Agent mode** from the dropdown at the top
3. Click the **Tools** button to view available tools
4. Enable shadcn tools

### Step 3: Verify Setup
In Copilot Chat, try:
```
use shadcn to list all components available
```

You should see a list of all shadcn/ui components!

---

## 🎨 Using Shadcn Components in Chat Interface

Once MCP is enabled, you can ask Copilot to help redesign the UI:

### Example Prompts:

**Get component details:**
```
use shadcn and show me details about the card component
```

**Redesign chat interface:**
```
use shadcn to help me redesign the ChatInterface component using:
- Card for message containers
- Button for send button  
- Input for text input
- ScrollArea for messages
- Badge for related topics
```

**Install specific components:**
```
use shadcn to show me how to add the card, button, input, scroll-area, and badge components
```

---

## 📦 Manual Installation (if needed)

If you prefer to install shadcn/ui manually:

```bash
cd chrome-extension

# Initialize shadcn/ui
npx shadcn@latest init

# Install needed components
npx shadcn@latest add card
npx shadcn@latest add button
npx shadcn@latest add input
npx shadcn@latest add scroll-area
npx shadcn@latest add badge
npx shadcn@latest add separator
```

---

## 🐛 Testing Auto-Close Fix

After reloading the extension, test:

1. Navigate to: `https://luminate.centennialcollege.ca/ultra/stream`
2. Click extension icon to open side panel
3. Navigate to: `https://google.com`

**Expected:**
- Console log: `🚪 Side panel DISABLED (not on /ultra/)`
- Console log: `🔒 Attempted to close side panel`
- Side panel should close automatically

**Note:** Chrome's Side Panel API might not support programmatic closing in all versions. If it doesn't close automatically, that's a Chrome limitation. The side panel will be disabled (grayed icon) and won't be accessible until you return to a `/ultra/` page.

---

## 📝 Next: Redesign with Shadcn

Once shadcn MCP is working, we can:

1. Install shadcn/ui components
2. Update `ChatInterface.tsx` to use shadcn components
3. Improve the UI/UX with proper design system
4. Add animations and better loading states
5. Improve accessibility

Ask Copilot with MCP to help generate the new ChatInterface code!
