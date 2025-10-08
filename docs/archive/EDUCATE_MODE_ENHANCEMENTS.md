# Educate Mode Enhancements: Stop, Rerun, and Branch Navigation

## ✅ Completed

### 1. Branch UI Components Created (`branch.tsx`)
Location: `/chrome-extension/src/components/ai/branch.tsx`

**Components:**
- `Branch` - Container managing branch state
- `BranchMessages` - Displays current branch content
- `BranchSelector` - Navigation controls container
- `BranchPrevious` - Previous branch button
- `BranchNext` - Next branch button  
- `BranchPage` - Shows "1 / 3" indicator

**Features:**
- ✅ Context-based state management
- ✅ Keyboard navigation support
- ✅ Automatic hiding when only 1 branch
- ✅ Smooth transitions
- ✅ TypeScript typed
- ✅ shadcn/ui styled

## 🚧 In Progress

### 2. EducateMode Updates Needed

**File**: `/chrome-extension/src/components/EducateMode.tsx`

**Required Changes:**

#### A. Update ChatMessage Interface ✅
```typescript
interface ResponseBranch {
  content: string;
  reasoning?: string;
  confidence?: number;
}

interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;  // Current branch content
  branches?: ResponseBranch[];  // Multiple response variations
  currentBranch?: number;  // Currently selected branch index
  timestamp: Date;
  reasoning?: string;
  confidence?: number;
  isStreaming?: boolean;
  fullContent?: string;
}
```

#### B. Add Streaming Control ✅
```typescript
const streamIntervalRef = useRef<NodeJS.Timeout | null>(null);
const currentMessageRef = useRef<string | null>(null);

const stopStreaming = useCallback(() => {
  if (streamIntervalRef.current) {
    clearInterval(streamIntervalRef.current);
    streamIntervalRef.current = null;
  }
  setIsLoading(false);
  
  // Mark current message as complete
  if (currentMessageRef.current) {
    setMessages(prev => prev.map(msg => 
      msg.id === currentMessageRef.current 
        ? { ...msg, isStreaming: false }
        : msg
    ));
    currentMessageRef.current = null;
  }
}, []);
```

#### C. Add Rerun Function
```typescript
const handleRerun = useCallback(async (messageId: string) => {
  const messageIndex = messages.findIndex(msg => msg.id === messageId);
  if (messageIndex === -1) return;
  
  // Find the preceding user message
  let userQuery = '';
  for (let i = messageIndex - 1; i >= 0; i--) {
    if (messages[i].role === 'user') {
      userQuery = messages[i].content;
      break;
    }
  }
  
  if (!userQuery) return;
  
  setIsLoading(true);
  
  try {
    // Call API to get new variation
    const apiResponse = await queryUnified(userQuery);
    let responseContent = apiResponse.response.formatted_response;
    const reasoning = apiResponse.reasoning;
    const confidence = apiResponse.confidence;
    
    if (apiResponse.mode === 'navigate') {
      const confidencePercent = (confidence * 100).toFixed(0);
      responseContent = `🔵 **Switched to Navigate Mode** (${confidencePercent}% confidence)\\n\\n` +
        `*This query is better suited for quick information retrieval.*\\n\\n---\\n\\n${responseContent}`;
    }
    
    // Add new branch to the message
    setMessages(prev => prev.map(msg => {
      if (msg.id === messageId) {
        const branches = msg.branches || [{ content: msg.content, reasoning: msg.reasoning, confidence: msg.confidence }];
        const newBranches = [...branches, { content: responseContent, reasoning, confidence }];
        return {
          ...msg,
          branches: newBranches,
          currentBranch: newBranches.length - 1,  // Switch to new branch
          content: responseContent,
          reasoning,
          confidence,
          fullContent: responseContent,
          isStreaming: true
        };
      }
      return msg;
    }));
    
    // Stream the new response
    currentMessageRef.current = messageId;
    let index = 0;
    streamIntervalRef.current = setInterval(() => {
      if (index < responseContent.length) {
        setMessages(prev => prev.map(msg =>
          msg.id === messageId
            ? { ...msg, content: responseContent.substring(0, index + 1) }
            : msg
        ));
        index += 1;
      } else {
        if (streamIntervalRef.current) {
          clearInterval(streamIntervalRef.current);
          streamIntervalRef.current = null;
        }
        setMessages(prev => prev.map(msg =>
          msg.id === messageId ? { ...msg, isStreaming: false } : msg
        ));
        setIsLoading(false);
        currentMessageRef.current = null;
      }
    }, 10);
  } catch (error) {
    console.error('Rerun error:', error);
    setIsLoading(false);
  }
}, [messages]);
```

#### D. Update handleSubmit to Use Refs
In the handleSubmit function, replace:
```typescript
const streamInterval = setInterval(() => {
  // ... streaming logic
  clearInterval(streamInterval);
}, 15);
```

With:
```typescript
currentMessageRef.current = messageId;
streamIntervalRef.current = setInterval(() => {
  // ... streaming logic
  if (streamIntervalRef.current) {
    clearInterval(streamIntervalRef.current);
    streamIntervalRef.current = null;
  }
  currentMessageRef.current = null;
}, 10);
```

Also add initial branch:
```typescript
const assistantMessage: ChatMessage = {
  id: messageId,
  role: 'assistant',
  content: '',
  fullContent: responseContent,
  timestamp: new Date(),
  reasoning,
  confidence,
  isStreaming: true,
  branches: [{ content: responseContent, reasoning, confidence }],  // ADD THIS
  currentBranch: 0  // ADD THIS
};
```

#### E. Update Message Rendering to Include Branches

Replace the message rendering section with:

```typescript
{messages.map((message) => {
  // For assistant messages with branches
  if (message.role === 'assistant' && message.branches && message.branches.length > 0) {
    const totalBranches = message.branches.length;
    const currentBranch = message.currentBranch || 0;
    
    return (
      <div key={message.id}>
        <Branch
          totalBranches={totalBranches}
          defaultBranch={currentBranch}
          onBranchChange={(branchIndex) => {
            // Update current branch when user navigates
            setMessages(prev => prev.map(msg =>
              msg.id === message.id
                ? {
                    ...msg,
                    currentBranch: branchIndex,
                    content: msg.branches![branchIndex].content,
                    reasoning: msg.branches![branchIndex].reasoning,
                    confidence: msg.branches![branchIndex].confidence
                  }
                : msg
            ));
          }}
        >
          <MessageBubble
            role={message.role}
            timestamp={message.timestamp}
            isStreaming={message.isStreaming || false}
            mode="educate"
          >
            <BranchMessages>
              {message.branches.map((branch, idx) => (
                <Response key={idx} parseIncompleteMarkdown={true}>
                  {idx === currentBranch ? message.content : branch.content}
                </Response>
              ))}
            </BranchMessages>

            {/* Message Actions */}
            {!message.isStreaming && (
              <Actions className="mt-3">
                {/* Stop button (only when streaming) */}
                {message.isStreaming && (
                  <Action
                    label="Stop"
                    tooltip="Stop generating"
                    onClick={stopStreaming}
                  >
                    <Square className="h-4 w-4" />
                  </Action>
                )}
                
                {/* Rerun button */}
                <Action
                  label="Rerun"
                  tooltip="Generate new variation"
                  onClick={() => handleRerun(message.id)}
                  disabled={isLoading}
                >
                  <RotateCcw className="h-4 w-4" />
                </Action>
                
                <Action
                  label="Copy response"
                  tooltip="Copy explanation"
                  onClick={async () => {
                    await copyToClipboard(message.content);
                  }}
                >
                  <Copy className="h-4 w-4" />
                </Action>
                <Action
                  label="Helpful"
                  tooltip="This helped me learn"
                  onClick={() => console.log('Helpful')}
                >
                  <ThumbsUp className="h-4 w-4" />
                </Action>
                <Action
                  label="Not helpful"
                  tooltip="I need more clarification"
                  onClick={() => console.log('Not helpful')}
                >
                  <ThumbsDown className="h-4 w-4" />
                </Action>
              </Actions>
            )}

            {/* Branch Navigation */}
            <BranchSelector from={message.role}>
              <BranchPrevious />
              <BranchPage />
              <BranchNext />
            </BranchSelector>

            {/* Reasoning Section */}
            {message.reasoning && (
              <Reasoning className="mt-4">
                <ReasoningTrigger>
                  <Lightbulb className="h-4 w-4" />
                  Why this response?
                </ReasoningTrigger>
                <ReasoningContent>{message.reasoning}</ReasoningContent>
              </Reasoning>
            )}
          </MessageBubble>
        </Branch>
      </div>
    );
  }
  
  // Regular message rendering for user messages and simple assistant messages
  return (
    <div key={message.id}>
      <MessageBubble
        role={message.role}
        timestamp={message.timestamp}
        isStreaming={message.isStreaming || false}
        mode="educate"
      >
        <Response parseIncompleteMarkdown={true}>
          {message.content}
        </Response>

        {/* Actions for non-branched messages */}
        {message.role === 'assistant' && !message.isStreaming && (
          <Actions className="mt-3">
            <Action
              label="Rerun"
              tooltip="Generate new variation"
              onClick={() => handleRerun(message.id)}
              disabled={isLoading}
            >
              <RotateCcw className="h-4 w-4" />
            </Action>
            <Action
              label="Copy response"
              tooltip="Copy explanation"
              onClick={async () => {
                await copyToClipboard(message.content);
              }}
            >
              <Copy className="h-4 w-4" />
            </Action>
          </Actions>
        )}
      </MessageBubble>
    </div>
  );
})}
```

#### F. Add Stop Button to PromptInput

Update the PromptInput section:

```typescript
<PromptInput
  onSubmit={handleSubmit}
  onStop={stopStreaming}  // ADD THIS
  disabled={false}
  isStreaming={isLoading}  // ADD THIS
  placeholder="Ask me to explain a concept..."
  mode="educate"
/>
```

## 📋 Implementation Checklist

- [x] Create branch.tsx component
- [ ] Update ChatMessage interface with branches
- [ ] Add stopStreaming function
- [ ] Add handleRerun function  
- [ ] Update handleSubmit to use refs
- [ ] Update message rendering with Branch components
- [ ] Add stop/rerun action buttons
- [ ] Update PromptInput props
- [ ] Test stop button during streaming
- [ ] Test rerun creates new branch
- [ ] Test branch navigation (prev/next)
- [ ] Test branch indicator shows correct numbers
- [ ] Test keyboard navigation

## 🎯 Expected User Experience

### Stop Button
- Appears while response is streaming
- Click to immediately halt generation
- Message marks as complete (not streaming)
- Can still read partial response

### Rerun Button
- Appears after response completes
- Click to generate new variation
- Creates new branch automatically
- Shows "1 / 2" indicator
- Can navigate between variations

### Branch Navigation
- Arrows appear when 2+ branches exist
- Click left/right to switch versions
- Smooth transition between branches
- Preserves all variations
- Shows current position (e.g., "2 / 3")

## 🐛 Edge Cases to Handle

1. **Stop during first character**: Should not create empty message
2. **Rerun while streaming**: Should be disabled
3. **Multiple reruns quickly**: Should queue or prevent
4. **Branch limit**: Consider max 5-7 branches, auto-prune old ones
5. **Memory**: Each branch stores full content - monitor RAM usage

## 🚀 Testing Commands

```bash
# 1. Restart backend
cd development/backend
python fastapi_service/main.py

# 2. Rebuild extension
cd chrome-extension
npm run build

# 3. Reload in Chrome
chrome://extensions/ → Reload "Luminate AI"
```

## 🎨 UI Preview

```
┌─────────────────────────────────────────────────┐
│ 🎓 Luminate AI (Educate Mode)                   │
├─────────────────────────────────────────────────┤
│                                                 │
│ [Response content with LaTeX formulas]          │
│                                                 │
│ ┌───────────────────────────────────────────┐  │
│ │ 🔄 Rerun  📋 Copy  👍 Helpful  👎 Not     │  │
│ └───────────────────────────────────────────┘  │
│                                                 │
│ ◀ 2 / 3 ▶  [Branch navigation]                 │
│                                                 │
│ 💡 Why this response? [Collapsible reasoning]  │
└─────────────────────────────────────────────────┘
```

During streaming:
```
┌─────────────────────────────────────────────────┐
│ [Partial response...]                           │
│                                                 │
│ ⏹ Stop  [Button to halt generation]            │
└─────────────────────────────────────────────────┘
```

## 📝 Notes

- Branch state is in-memory only (not persisted across refresh)
- Each rerun calls the API again (uses tokens)
- Branches are per-message, not global
- Stop button stops current stream only
- Rerun uses the original user query

## 🎉 Benefits

- **Stop**: Save time and tokens on bad responses
- **Rerun**: Get better answers without losing good ones
- **Branches**: Compare variations like ChatGPT
- **Navigation**: Easy switching between options
- **Memory**: All variations preserved until refresh

