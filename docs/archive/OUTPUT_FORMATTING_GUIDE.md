# Backend-Frontend Output Formatting Guide

This guide documents the alignment between backend API responses and frontend UI components for Luminate AI.

## 📋 Overview

The backend has been enhanced to format responses specifically for the frontend UI components, ensuring seamless integration between the orchestrator, Navigate mode, Educate mode, and the React UI.

---

## 🎯 Unified Query Response Structure

### Base Response Format

```typescript
interface UnifiedQueryResponse {
  mode: 'navigate' | 'educate';
  confidence: number;  // 0-1
  reasoning: string;
  response: ResponseData;
  timestamp: string;
}
```

### Frontend UI Component Mapping

| Field | UI Component | Purpose |
|-------|-------------|---------|
| `mode` | Mode indicator badge | Shows which mode handled the query |
| `confidence` | Confidence percentage | Displays routing confidence |
| `reasoning` | `ReasoningTrigger`/`ReasoningContent` | Shows why orchestrator chose this mode |
| `response.formatted_response` | `Response` component | Main markdown content |
| `response.top_results` | `Sources` component | Clickable source cards |
| `response.related_topics` | `Suggestion` components | Clickable topic chips |
| `response.external_resources` | `ExternalResources` | YouTube, web links |
| `response.quiz_suggestion` | `QuizDialog` trigger | Opens quiz modal |
| `response.next_steps` | Action buttons | Suggested next actions |

---

## 🔍 Navigate Mode Output Format

### Purpose
Fast retrieval of course materials with external resources.

### Response Structure

```typescript
{
  mode: "navigate",
  confidence: 0.85,
  reasoning: "Query seeks specific course content about neural networks",
  response: {
    formatted_response: "## Neural Networks\n\nHere's what I found...",
    
    // Sources UI Component
    top_results: [
      {
        title: "Neural Networks Introduction",
        excerpt: "A neural network is...", // Max 200 chars
        live_url: "https://luminate.centennialcollege.ca/...",
        module: "Module 3",
        relevance_explanation: "Covers core neural network concepts",
        content_type: "document"
      }
    ],
    
    // Suggestion UI Component
    related_topics: [
      {
        title: "Backpropagation",
        why_explore: "Learn how neural networks learn"
      },
      {
        title: "Activation Functions",
        why_explore: "Understand neuron activation"
      }
    ],
    
    // ExternalResources Component
    external_resources: [
      {
        title: "3Blue1Brown - Neural Networks",
        url: "https://youtube.com/...",
        type: "video",
        channel: "3Blue1Brown"
      }
    ],
    
    // Quiz Trigger (optional)
    quiz_suggestion: {
      topic: "Neural Networks",
      difficulty: "medium",
      question_count: 5,
      prompt: "💡 Test your knowledge of Neural Networks"
    },
    
    total_results: 5
  },
  timestamp: "2025-10-07T..."
}
```

### Field Details

#### `top_results` (for Sources Component)
- **title**: Document/topic title
- **excerpt**: First 200 chars of content
- **live_url**: Blackboard or external URL
- **module**: Course module name
- **relevance_explanation**: Why this result is relevant
- **content_type**: 'document', 'video', 'assignment', etc.

#### `related_topics` (for Suggestion Components)
- **title**: Topic name (clickable)
- **why_explore**: Tooltip text explaining relevance

#### `quiz_suggestion` (Triggers QuizDialog)
Appears when:
- Query contains keywords: 'test', 'quiz', 'practice', 'assess'
- OR when 3+ relevant results are found
- Automatically extracts topic from first result

---

## 🎓 Educate Mode Output Format

### Purpose
Deep conceptual learning with 4-level explanations and scaffolding.

### Response Structure

```typescript
{
  mode: "educate",
  confidence: 0.95,
  reasoning: "Query requests conceptual explanation with 'explain gradient descent'",
  response: {
    formatted_response: `
## 🎯 Gradient Descent Explained

### Level 1: Intuition (ELI5)
Imagine you're blindfolded on a hill...

### Level 2: Mathematical Notation
θ_new = θ_old - α ∇J(θ)

### Level 3: Code Implementation
\`\`\`python
theta = theta - alpha * gradient
\`\`\`

### Level 4: Common Misconceptions
❌ Bigger learning rate = faster learning
✅ Too big → overshoot!
`,
    
    level: "4-level-translation",  // or "conceptual", "adaptive"
    
    // Math Translation metadata
    math_translation: {
      available: true,
      levels: ["intuition", "mathematical", "code", "misconceptions"]
    },
    
    // Quiz Trigger
    quiz_suggestion: {
      topic: "Gradient Descent",
      difficulty: "medium",
      question_count: 5,
      prompt: "🎯 Ready to test your understanding of Gradient Descent?"
    },
    
    // Action suggestions with emojis
    next_steps: [
      "💻 Try implementing the code",
      "🔄 Practice with variations",
      "📊 Compare different approaches"
    ],
    
    misconceptions_detected: [],
    
    // Optional: Related content for deeper learning
    related_topics: [
      {
        title: "Stochastic Gradient Descent",
        why_explore: "Learn the faster variant"
      }
    ]
  },
  timestamp: "2025-10-07T..."
}
```

### Field Details

#### `level` Types
- **4-level-translation**: Full intuition → math → code → misconceptions
- **conceptual**: RAG-based explanation
- **adaptive**: Personalized based on student mastery

#### `math_translation`
Indicates if response includes 4-level breakdown:
- Level 1: Plain language intuition
- Level 2: Mathematical notation
- Level 3: Code implementation
- Level 4: Common misconceptions

#### `next_steps`
Action-oriented suggestions with emojis:
- Use emojis for visual clarity (💻 📚 🧮 💬 🔄 📊)
- Keep suggestions specific and actionable

#### `quiz_suggestion`
Always included in Educate mode responses to:
- Reinforce learning
- Test understanding immediately
- Provide adaptive difficulty

---

## 🎨 Frontend UI Component Requirements

### Sources Component

Expects array of objects with:
```typescript
{
  title: string;
  excerpt: string;  // Max 200 chars
  live_url?: string;
  module: string;
  relevance_explanation: string;
}
```

### Suggestion Component

Expects array of objects with:
```typescript
{
  title: string;
  why_explore: string;  // Shows on hover
}
```

### QuizDialog Trigger

Expects object with:
```typescript
{
  topic: string;
  difficulty: 'easy' | 'medium' | 'hard';
  question_count: number;
  prompt: string;  // Display message
}
```

### ExternalResources Component

Expects array of objects with:
```typescript
{
  title: string;
  url: string;
  type: 'video' | 'article' | 'tutorial';
  channel?: string;  // For videos
}
```

---

## 🔄 Orchestrator Mode Selection

### Mode Indicators in UI

When orchestrator routes to non-expected mode:

**Navigate → Educate**:
```
🟣 **Switched to Educate Mode** (95% confidence)

*This query is better suited for deep learning explanations.*

---

[Main response content]
```

**Educate → Navigate**:
```
🔵 **Switched to Navigate Mode** (87% confidence)

*This query is better suited for quick information retrieval.*

---

[Main response content]
```

---

## 🎯 Quiz Suggestion Triggers

### Navigate Mode
Quiz suggested when:
1. Query contains: `test`, `quiz`, `practice`, `assess`, `check understanding`, `evaluate`
2. OR: Response has 3+ relevant results (sufficient content to quiz on)

### Educate Mode
Quiz **always** suggested after:
- 4-level translations
- Conceptual explanations
- To reinforce learning immediately

### Quiz Topic Extraction

**Navigate Mode**:
- Use first result title
- Or first related topic

**Educate Mode**:
- Extract keywords from query (words > 4 chars)
- Take first 3 keywords as topic

---

## 📝 Next Steps Formatting

### Use Emojis for Visual Clarity

| Emoji | Meaning | Example |
|-------|---------|---------|
| 💻 | Code/Implementation | "Try implementing the code" |
| 📚 | Study/Review | "Review the course materials" |
| 🧮 | Practice | "Practice related problems" |
| 💬 | Questions | "Ask follow-up questions" |
| 🔄 | Variations | "Try with different parameters" |
| 📊 | Compare/Analyze | "Compare different approaches" |
| 🎯 | Goal/Challenge | "Test yourself with a quiz" |

### Format
```typescript
next_steps: [
  "💻 Action 1 with emoji",
  "📚 Action 2 with emoji",
  "🧮 Action 3 with emoji"
]
```

---

## 🧪 Testing the Formatting

### Navigate Mode Test

**Query**: "Show me content about neural networks"

**Expected Response**:
- ✅ 3-5 top_results with titles, excerpts, URLs
- ✅ 2-3 related_topics
- ✅ external_resources (YouTube, etc.)
- ✅ quiz_suggestion with topic "Neural Networks"

### Educate Mode Test

**Query**: "Explain gradient descent in 4 levels"

**Expected Response**:
- ✅ formatted_response with 4-level structure
- ✅ math_translation.available = true
- ✅ quiz_suggestion for "Gradient Descent"
- ✅ next_steps with 💻 🔄 📊 emojis

### Orchestrator Test

**Query**: "Find week 3 assignments"

**Expected**: Navigate mode (high confidence)
- Should NOT show mode switch indicator
- Response formatted for Sources component

**Query**: "Explain backpropagation step by step"

**Expected**: Educate mode (high confidence)
- Should NOT show mode switch indicator
- Response with conceptual or 4-level format

---

## 🐛 Common Formatting Issues

### Issue 1: Missing `live_url` in Sources

**Problem**: Frontend shows "No URL available"

**Solution**: Backend now checks multiple fields:
```python
'live_url': result.get('url') or result.get('live_url') or result.get('bb_url')
```

### Issue 2: Related Topics as Strings

**Problem**: Frontend expects objects with `title` and `why_explore`

**Solution**: Backend normalizes all formats:
```python
if isinstance(topic, str):
    formatted_topics.append({
        'title': topic,
        'why_explore': f'Learn more about {topic}'
    })
```

### Issue 3: Excerpt Too Long

**Problem**: UI layout breaks with long excerpts

**Solution**: Limit to 200 characters:
```python
'excerpt': result.get('excerpt', '')[:200]
```

---

## 📚 Summary

### Key Improvements

1. **Unified Response Structure**: Clear mapping to UI components
2. **Quiz Triggers**: Automatic suggestions based on content and keywords
3. **Normalized Formats**: Consistent field structure across modes
4. **Visual Enhancements**: Emojis in next_steps for better UX
5. **Graceful Fallbacks**: All optional fields have defaults

### Frontend Integration

The frontend components (`NavigateMode.tsx`, `EducateMode.tsx`) already:
- ✅ Extract `top_results` for Sources display
- ✅ Parse `related_topics` for Suggestions
- ✅ Show mode switch indicators based on `mode` field
- ✅ Display `reasoning` in collapsible sections

### Backend Enhancements

The backend now:
- ✅ Formats all responses for specific UI components
- ✅ Adds quiz suggestions intelligently
- ✅ Includes actionable next_steps with emojis
- ✅ Normalizes data from LangGraph workflows

---

**Last Updated**: October 7, 2025  
**Status**: ✅ Complete and Tested

