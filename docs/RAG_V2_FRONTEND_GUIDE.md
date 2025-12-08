# RAG v2 Frontend Visual Guide

## Source Display Enhancements

### Before (RAG v1)
```
📄 Sources (5)
  📄 Topic 1.2: The Turing test
     Module 1 - Topic 1.2 • Page 1
     
  📄 Topic 2.1: Intelligent Agents
     Module 2 - Topic 2.1 • Page 3
```

**Issues:**
- ❌ No indication of source type
- ❌ External URLs not shown
- ❌ Mediasite videos look like regular files
- ❌ No confidence indicators

---

### After (RAG v2)
```
📄 Sources (5)

  🌐 Topic 1.2: The Turing test  [EMBEDDED] [VIDEO]
     │ Module 1 - Topic 1.2
     │ 🔗 https://mediasite.centennialcollege.ca/Mediasite/Play/...
     └─ Contextual description...
     
  🌐 Topic 1.2: The Turing test  [EMBEDDED]
     │ Module 1 - Topic 1.2
     │ 🔗 https://computing.dcu.ie/~humphrys/turing.test.html
     └─ Contextual description...
     
  🌐 Topic 8.1: Introduction to ANN  [EMBEDDED]
     │ Module 8 - Topic 8.1
     │ 🔗 http://ai.berkeley.edu/home.html
     └─ Contextual description...
     
  📄 Topic 2.1: Intelligent Agents  [COURSE]
     Module 2 - Topic 2.1 • Page 3
     
  📄 Topic 6.3: Classification models  [COURSE]
     Module 6 - Topic 6.3 • Page 12
```

**Improvements:**
- ✅ **Icon differentiation**: 🎥 Video, 🌐 Globe for embedded, 📖 Book for OER, 📄 File for course
- ✅ **Source type badges**: Clear visual indicators (COURSE/OER/EMBEDDED)
- ✅ **Video badge**: Prominent "VIDEO" badge for mediasite links
- ✅ **Blue accent**: Mediasite sources get blue left border
- ✅ **Clickable URLs**: External links open in new tab
- ✅ **Confidence scoring**: Backend tracks high/medium/low (can be shown in future)

---

## Badge Styling

### Course Materials (Default Badge)
```
[COURSE]
```
- Color: Default (primary)
- Icon: 📄 FileText
- Priority: Highest (boost +0.25)

### OER Resources (Secondary Badge)
```
[OER]
```
- Color: Secondary (muted)
- Icon: 📖 BookOpen
- Priority: Medium (boost 0.0)
- Example: MIT Math for ML textbook

### Embedded Resources (Outline Badge)
```
[EMBEDDED]
```
- Color: Outline (border only)
- Icon: 🌐 Globe (or 🎥 Video for mediasite)
- Priority: High (boost +0.10)
- Types: Mediasite videos, Wikipedia, external sites

### Video Badge (Special)
```
[VIDEO]
```
- Color: Outline with blue border
- Only shown for mediasite links
- Stacks next to [EMBEDDED] badge

---

## Component Structure

```tsx
<Sources count={5}>
  <SourcesTrigger />
  <SourcesContent>
    <LazySource
      title="Topic 1.2: The Turing test"
      href="https://mediasite.centennialcollege.ca/..."
      source_type="embedded"
      link_type="mediasite"
      citation_confidence="high"
    >
      {/* Renders as: */}
      <div className="border-l-4 border-l-blue-500">
        🎥 [Blue icon]
        Title [EMBEDDED] [VIDEO]
        🔗 [mediasite URL]
        Description...
      </div>
    </LazySource>
  </SourcesContent>
</Sources>
```

---

## Inline Citations

The LLM receives citation confidence scores and decides which sources to cite:

**Response text:**
```
The Turing test is a well-known concept in AI, designed to assess 
a machine's ability to exhibit intelligent behavior equivalent to, 
or indistinguishable from, a human [1], [2].

Think of it like this: you're having a text conversation with two 
hidden entities, one human and one AI.

What criteria would you use to determine which is which?
```

**Citation mapping:**
- `[1]` → External URL (medium confidence) - used for definition
- `[2]` → Mediasite video (high confidence) - used for detailed explanation
- Sources 3-5 → Not cited inline (lower relevance or not directly used)

**Benefits:**
- ✅ Only high-relevance sources cited inline
- ✅ Other sources available in expandable "Sources" section
- ✅ Prevents citation spam
- ✅ LLM decides based on actual usage in response

---

## Mobile Responsive Design

### Badges wrap gracefully on small screens:
```
┌────────────────────────────────────┐
│ 🎥 Topic 1.2: The Turing test      │
│ [EMBEDDED] [VIDEO]                  │
│                                     │
│ Module 1 - Topic 1.2               │
│ 🔗 https://mediasite...            │
│                                     │
│ Contextual description about the   │
│ Turing test video lecture...       │
└────────────────────────────────────┘
```

### Desktop view with inline badges:
```
┌──────────────────────────────────────────────────────────────┐
│ 🎥 Topic 1.2: The Turing test  [EMBEDDED] [VIDEO]             │
│                                                                │
│ Module 1 - Topic 1.2                                          │
│ 🔗 https://mediasite.centennialcollege.ca/...                │
│                                                                │
│ Contextual description about the Turing test video lecture    │
│ covering the imitation game and its philosophical implications │
└──────────────────────────────────────────────────────────────┘
```

---

## Color Palette

| Source Type | Border | Icon Color | Badge Variant |
|-------------|--------|------------|---------------|
| Course | Default | text-muted-foreground | default (primary) |
| OER | Default | text-muted-foreground | secondary (muted) |
| Embedded | Default | text-muted-foreground | outline |
| Mediasite | **Blue (left)** | **text-blue-500** | outline (blue) |

---

## Animation Behavior

1. **Sources expand** → Auto-expand when new sources arrive
2. **Staggered fade-in** → Each source card animates in sequence (50ms delay)
3. **Description lazy load** → Skeleton → LLM-generated description → Fade in
4. **Auto-collapse** → After 2 seconds (can be disabled)
5. **Hover effects** → Border highlight, slight background color change

---

## Accessibility

- ✅ **Keyboard navigation**: Tab through sources, Enter to open links
- ✅ **Screen readers**: Badges announced as "Source type: Course/OER/Embedded"
- ✅ **Color contrast**: All badges meet WCAG AA standards
- ✅ **Focus indicators**: Clear focus rings on interactive elements
- ✅ **Alt text**: Icon meanings conveyed through aria-labels

---

## Future UI Enhancements

### Phase 1: Confidence Indicators
```
🎥 Topic 1.2: The Turing test  [EMBEDDED] [VIDEO] ⭐⭐⭐
                                                   ^ High confidence
```

### Phase 2: Source Filters
```
📄 Sources (5)  [Filter: All ▼]
                └─ Course (2)
                └─ OER (0)
                └─ Embedded (3)
```

### Phase 3: Inline Video Player
```
🎥 Topic 1.2: The Turing test  [EMBEDDED] [VIDEO] [▶️ Play]
```

### Phase 4: Source Analytics
```
📊 Most helpful sources this week:
   1. Topic 1.2: The Turing test (32 clicks)
   2. Topic 8.1: Introduction to ANN (28 clicks)
```

---

## Developer Notes

### Adding new icons:
```tsx
import { Video, BookOpen, Globe, FileText } from "lucide-react"

const Icon = linkType === "mediasite" 
  ? Video 
  : sourceType === "oer" 
    ? BookOpen 
    : sourceType === "embedded" 
      ? Globe 
      : FileText
```

### Custom badge colors:
```tsx
const badgeVariant = sourceType === "course" 
  ? "default"  // Primary color
  : sourceType === "oer" 
    ? "secondary"  // Muted color
    : "outline"  // Border only
```

### Blue accent for videos:
```tsx
className={cn(
  "block rounded-md bg-card/50 p-3 transition-all border border-border/50",
  linkType === "mediasite" && "border-l-4 border-l-blue-500",
)}
```

---

*Last Updated: December 2024*  
*Design System: shadcn/ui + Tailwind CSS*  
*Icons: Lucide React*
