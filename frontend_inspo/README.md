# Luminate AI - Agentic AI Tutor


A Chrome extension sidepanel featuring an intelligent AI tutor built with Next.js, AI SDK Elements, and Plasmo Framework.

## Features

- **Agentic AI Chat**: Interactive conversational AI with reasoning capabilities
- **AI SDK Elements**: Full integration of React AI components including:
  - Code Block with syntax highlighting and copy functionality
  - Inline Citations with hover cards
  - Reasoning display (collapsible thinking process)
  - Sources with web search results
  - Task tracking with status indicators
  - Tool execution visualization
  - AI-generated images
  - Smart suggestions for follow-up questions
- **Chrome Extension**: Runs in the browser sidepanel for easy access
- **Dark/Light Mode**: Shadcn green theme with theme switching
- **Settings Panel**: Toggle internet search and navigation features
- **Model Selection**: Switch between different AI models
- **File Attachments**: Upload and reference files in conversations
- **Navigation Rail**: Quick access to chat, history, and settings

## Tech Stack

- **Framework**: Next.js 16 (App Router)
- **UI**: shadcn/ui + Radix UI components
- **Styling**: Tailwind CSS v4
- **AI SDK**: Vercel AI SDK with AI Elements
- **Extension**: Plasmo Framework compatible
- **Syntax Highlighting**: react-syntax-highlighter
- **Markdown**: react-markdown

## Getting Started

### Development

\`\`\`bash
npm install
npm run dev
\`\`\`

Open [http://localhost:3000/sidepanel](http://localhost:3000/sidepanel) to view the chat interface.

### Building for Production

\`\`\`bash
npm run build
\`\`\`

### Chrome Extension Setup

1. Load the extension in Chrome:
   - Open `chrome://extensions/`
   - Enable "Developer mode"
   - Click "Load unpacked"
   - Select the `public` directory from this project

2. The extension manifest is located at `public/manifest.json`

3. Click the extension icon to open the sidepanel

## Project Structure

\`\`\`
├── app/
│   ├── sidepanel/
│   │   └── page.tsx          # Main chat interface
│   └── globals.css           # Global styles with design tokens
├── components/
│   ├── ai-elements/          # AI SDK Elements components
│   │   ├── code-block.tsx
│   │   ├── inline-citation.tsx
│   │   ├── task.tsx
│   │   ├── tool.tsx
│   │   ├── image.tsx
│   │   └── suggestion.tsx
│   ├── chat/                 # Chat-specific components
│   │   ├── conversation.tsx
│   │   ├── message.tsx
│   │   ├── prompt-input.tsx
│   │   ├── reasoning.tsx
│   │   ├── sources.tsx
│   │   ├── settings-panel.tsx
│   │   ├── chat-controls.tsx
│   │   └── chat-history.tsx
│   ├── nav-rail.tsx          # Right-side navigation
│   └── theme-toggle.tsx      # Dark/light mode switcher
├── hooks/
│   └── use-chat.ts           # Chat state management
├── types/
│   └── index.ts              # TypeScript types
└── public/
    ├── manifest.json         # Chrome extension manifest
    └── sidepanel.html        # Extension entry point
\`\`\`

## AI Elements Components

The app demonstrates all major AI SDK Elements:

- **Actions**: Message-level actions (copy, retry)
- **Code Block**: Syntax-highlighted code with copy button
- **Inline Citation**: Citation pills with hover cards showing sources
- **Reasoning**: Collapsible AI thinking process
- **Sources**: Web search results with expandable details
- **Task**: Progress tracking for multi-step operations
- **Tool**: Function call visualization with args/results
- **Image**: AI-generated or referenced images
- **Suggestion**: Quick follow-up prompts
- **Loader**: Streaming indicators

## Sample Conversation

The app includes a comprehensive sample conversation demonstrating:
- Complex reasoning about quantum computing
- Web search with multiple sources
- Python code example with syntax highlighting
- Inline citations in natural text
- Task and tool execution tracking
- Follow-up suggestions

## Customization

### Theming

Edit `app/globals.css` to customize the color scheme. The current theme uses shadcn green with a deep dark navy background.

### AI Models

Update the model list in `components/chat/prompt-input.tsx` to add or remove available models.

### Extension Settings

Modify `public/manifest.json` to change extension name, permissions, or icons.

## Development with Plasmo

This project is designed to be compatible with the Plasmo Framework for browser extension development.

### Converting to Plasmo

1. Create a new Plasmo project:
\`\`\`bash
pnpm create plasmo
\`\`\`

2. Copy the following files to your Plasmo project:
   - `sidepanel.tsx` (create from `app/sidepanel/page.tsx`)
   - All components from `components/`
   - Update `package.json` with required dependencies

3. Run development server:
\`\`\`bash
pnpm dev
\`\`\`

4. Load the extension in Chrome from the `build/chrome-mv3-dev` directory

### Key Plasmo Resources

- [Plasmo Framework Documentation](https://docs.plasmo.com/)
- [Plasmo Itero Cloud Platform](https://docs.plasmo.com/itero)
- [Chrome Extension Sidepanel API](https://developer.chrome.com/docs/extensions/reference/api/sidePanel)

## License

MIT
