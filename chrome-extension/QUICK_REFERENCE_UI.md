# 🚀 Quick Reference: New UI Components

## 📦 Available Hooks

### Import
```typescript
import { 
  useLocalStorage, 
  useCopyToClipboard, 
  useDebounceValue,
  useIsClient,
  useDarkMode 
} from '@/hooks'
```

### Usage

**useLocalStorage**
```typescript
const [value, setValue] = useLocalStorage('key', defaultValue)
```

**useCopyToClipboard**
```typescript
const [copiedText, copy] = useCopyToClipboard()
await copy('text to copy')
```

**useDebounceValue**
```typescript
const debouncedValue = useDebounceValue(value, 500)
```

**useIsClient**
```typescript
const isClient = useIsClient()
if (!isClient) return null
```

**useDarkMode**
```typescript
const { isDark, toggle, setIsDark } = useDarkMode()
```

---

## 🎨 UI Components

### CodeBlock
```typescript
import { CodeBlock } from '@/components/ui/code-block'

<CodeBlock 
  language="python"
  code={codeString}
/>
```

### CopyButton
```typescript
import { CopyButton } from '@/components/ui/copy-button'

<CopyButton 
  text="Copy this"
  variant="ghost"
  size="icon"
/>
```

### ThemeToggle
```typescript
import { ThemeToggle } from '@/components/ui/theme-toggle'

<ThemeToggle />
```

### Response (Enhanced)
```typescript
import { Response } from '@/components/ui/response'

<Response 
  content={markdownString}
  isStreaming={false}
/>
```

---

## 🌈 Theme Provider

### Setup
```typescript
import { ThemeProvider } from '@/components/providers/theme-provider'

<ThemeProvider
  attribute="class"
  defaultTheme="system"
  enableSystem
  disableTransitionOnChange
>
  {children}
</ThemeProvider>
```

### Use Theme
```typescript
import { useTheme } from 'next-themes'

const { theme, setTheme } = useTheme()
setTheme('dark') // or 'light', 'system'
```

---

## 🧪 Testing Examples

### Test Theme Toggle
```bash
1. Load extension
2. Click theme toggle (top-right)
3. Verify smooth transition
4. Reload - theme should persist
```

### Test Code Highlighting
```bash
Query: "Show me gradient descent in Python"
Expected: Code block with syntax highlighting + copy button
```

### Test Math Rendering
```bash
Query: "Explain the gradient descent formula"
Expected: LaTeX math rendered with KaTeX
```

### Test Markdown
```bash
Query: "Explain backpropagation"
Expected: Headers, bold, lists, code blocks formatted
```

---

## ✅ Build & Deploy

```bash
# Install dependencies
npm install

# Build extension
npm run build

# Load in Chrome
1. chrome://extensions/
2. Enable Developer Mode
3. Load unpacked → select dist/
```

---

## 📊 Component Props Reference

### CodeBlock Props
```typescript
interface CodeBlockProps {
  language: string        // Required: 'python', 'javascript', etc.
  code: string           // Required: code to highlight
  className?: string     // Optional: additional classes
}
```

### CopyButton Props
```typescript
interface CopyButtonProps {
  text: string                              // Required
  className?: string                        // Optional
  variant?: "default" | "ghost" | "outline" // Optional
  size?: "default" | "sm" | "lg" | "icon"  // Optional
}
```

### Response Props
```typescript
interface ResponseProps {
  content: string        // Required: markdown string
  isStreaming?: boolean  // Optional: show streaming animation
  className?: string     // Optional: additional classes
}
```

---

## 🎯 Common Patterns

### Streaming Response
```typescript
const [content, setContent] = useState('')

useEffect(() => {
  // Simulate streaming
  let index = 0
  const fullText = "Full response..."
  
  const interval = setInterval(() => {
    if (index < fullText.length) {
      setContent(fullText.slice(0, index++))
    } else {
      clearInterval(interval)
    }
  }, 20)
}, [])

return <Response content={content} isStreaming={content.length < fullText.length} />
```

### Copy with Feedback
```typescript
const [, copy] = useCopyToClipboard()

const handleCopy = async () => {
  const success = await copy(textToCopy)
  if (success) {
    toast.success('Copied!')
  }
}
```

### Persist Chat History
```typescript
const [messages, setMessages] = useLocalStorage('chat-history', [])

const addMessage = (msg) => {
  setMessages([...messages, msg])
}
```

---

## 🐛 Troubleshooting

### Theme not persisting
```typescript
// Ensure ThemeProvider wraps your app
// Check localStorage for 'theme' key
```

### Code not highlighting
```typescript
// Verify language is supported by Prism
// Check import: import { Highlight } from 'prism-react-renderer'
```

### Math not rendering
```typescript
// Ensure KaTeX CSS is imported
import 'katex/dist/katex.min.css'
```

### Build errors
```bash
# Clear cache and rebuild
rm -rf node_modules dist
npm install
npm run build
```
