# Luminate AI Chrome Extension

A Chrome extension that provides AI-powered course assistance for COMP237 students on Blackboard Learn Ultra.

## Features

- 🔍 **Navigate Mode**: Search and explore course content with AI assistance
- 💬 **Chat Interface**: Interactive chat with context-aware responses
- 📚 **Related Topics**: Discover connected concepts and learning paths
- 🎯 **Smart Positioning**: Button appears next to Blackboard's Help button

## Installation

### 1. Build the Extension

```bash
cd chrome-extension
npm install
npm run build
```

This creates a `dist/` folder with the compiled extension.

### 2. Load in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `chrome-extension/dist` folder
5. The Luminate AI extension should now appear in your extensions list

### 3. Start the Backend

The extension requires the Luminate AI backend to be running:

```bash
cd /Users/aazain/Documents/GitHub/luminate-ai
source .venv/bin/activate
uvicorn main:app --reload
```

Backend should be accessible at `http://localhost:8000`

## Usage

1. **Navigate to Any Luminate Blackboard Page**
   - Go to any page under: `https://luminate.centennialcollege.ca/ultra/...`
   - Works on: course pages, calendar, stream, grades, announcements, etc.
   - Example course page: `https://luminate.centennialcollege.ca/ultra/courses/_11378_1/outline`

2. **Open the Side Panel**
   - Click the Luminate AI extension icon in your Chrome toolbar
   - Or click the sparkles button (if visible on supported pages)
   - The chat interface opens in a side panel

3. **Ask Questions**
   - Type your question about course topics
   - Navigate Mode searches course content
   - Get explanations with related topics
   - Click related topics to explore further

## Development

### File Structure

```
chrome-extension/
├── manifest.json           # Extension configuration
├── popup.html             # Extension popup HTML
├── package.json           # npm dependencies
├── vite.config.ts         # Vite build configuration
├── tailwind.config.js     # Tailwind CSS configuration
├── postcss.config.js      # PostCSS configuration
├── tsconfig.json          # TypeScript configuration
└── src/
    ├── popup/
    │   ├── Popup.tsx      # Extension popup component
    │   └── index.tsx      # Popup entry point
    ├── content/
    │   ├── index.tsx      # Content script (button injection)
    │   └── content.css    # Content script styles
    ├── components/
    │   └── ChatInterface.tsx  # Main chat UI
    ├── services/
    │   └── api.ts         # Backend API integration
    ├── lib/
    │   └── utils.ts       # Utility functions
    └── background/
        └── index.ts       # Background service worker
```

### Development Commands

```bash
# Install dependencies
npm install

# Build for production
npm run build

# Build in watch mode (auto-rebuild on changes)
npm run watch

# Development mode with Vite dev server
npm run dev
```

### Making Changes

1. Edit source files in `src/`
2. Run `npm run build` or `npm run watch`
3. Reload extension in Chrome:
   - Go to `chrome://extensions/`
   - Click the reload icon on Luminate AI extension

## Tech Stack

- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite 5
- **Styling**: Tailwind CSS 3
- **UI Components**: shadcn/ui pattern (custom)
- **Icons**: lucide-react
- **Chrome API**: Manifest V3

## Backend Integration

The extension communicates with the FastAPI backend at `http://localhost:8000`.

### API Endpoint

**POST** `/langgraph/navigate`

Request:
```json
{
  "query": "What is supervised learning?"
}
```

Response:
```json
{
  "formatted_response": "Supervised learning is...",
  "top_results": [...],
  "related_topics": ["Classification", "Regression", ...],
  "next_steps": [...]
}
```

## Troubleshooting

### Extension Not Appearing on Course Pages

- Check that you're on a Blackboard Ultra course page
- URL should match: `luminate.centennialcollege.ca/ultra/courses/*/outline*`
- Check browser console (F12) for errors

### "Backend Not Running" Error

- Ensure backend is running: `uvicorn main:app --reload`
- Check backend health: `http://localhost:8000/health`
- Verify CORS settings allow extension origin

### Button Position Issues

- The button positions itself relative to Blackboard's Help button
- If Help button moves, our button moves too
- Fallback position: 140px from right edge

### Build Errors

```bash
# Clean install
rm -rf node_modules package-lock.json
npm install
npm run build
```

## Current Status

✅ **Completed:**
- Extension structure and configuration
- Popup menu with course detection
- Content script for button injection
- Chat interface with message history
- Backend API integration
- Build system with Vite + Tailwind

⏳ **To Add (Future):**
- Educate Mode (AI tutoring)
- Session persistence (save chat history)
- Keyboard shortcuts (Cmd+K to open)
- Markdown rendering in responses
- Code syntax highlighting

## Version

v1.0.0 - Navigate Mode MVP

## License

Centennial College - COMP237 Project
