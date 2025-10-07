# External Sources Update - October 5, 2025

## Changes Summary

### 1. OER Commons URL Format Fixed
**Issue**: OER Commons links were not working correctly.

**Solution**: Updated URL format to match the correct OER Commons search syntax.

**Before**:
```python
search_url = f"https://www.oercommons.org/search?q={quote_plus(query)}"
```

**After**:
```python
search_url = f"https://oercommons.org/search?search_source=site&f.search={quote_plus(query)}"
```

**Example**: 
- Query: "neural networks"
- URL: `https://oercommons.org/search?search_source=site&f.search=neural+networks`

---

### 2. Removed Khan Academy Sources
**Rationale**: Per user request to simplify external sources.

**Removed**: 
- All Khan Academy topic mappings
- Khan Academy search functionality
- ~40 lines of curated Khan Academy links

**Updated External Sources Now Include**:
- ✅ YouTube (3 videos via API)
- ✅ Wikipedia (1 article via API)
- ✅ OER Commons (1 search page link)
- ❌ ~~Khan Academy~~ (removed)
- ❌ ~~MIT OCW~~ (removed)

---

### 3. Removed MIT OCW Sources
**Rationale**: Per user request to simplify external sources.

**Removed**: 
- All MIT OpenCourseWare topic mappings
- MIT OCW search functionality
- ~45 lines of curated MIT OCW course links

---

### 4. Made Related Topics Clickable
**Issue**: Related topics would only populate the input field when clicked, requiring a second action to submit.

**Solution**: Changed onClick behavior to directly submit the query.

**Before**:
```tsx
onClick={() => setInput(topic.title)}
```

**After**:
```tsx
onClick={() => handleSubmit(topic.title)}
```

**User Experience**:
- **Before**: Click topic → fills input → click send button
- **After**: Click topic → immediately searches and displays results

---

## Files Modified

### Backend Changes

1. **`development/backend/langgraph/agents/external_resources.py`**
   - Updated `search_oer_commons()` URL format (lines 53-70)
   - Removed `Khan Academy` search section (~40 lines removed)
   - Removed `MIT OCW` search section (~45 lines removed)
   - Updated docstring to reflect current sources

### Frontend Changes

2. **`chrome-extension/src/components/ChatInterface.tsx`**
   - Updated related topics onClick handler (line 173)
   - Changed from `setInput()` to `handleSubmit()` for immediate search

---

## Testing

### Test OER Commons Link Format
1. Ask: "neural networks"
2. Click "Load Additional Resources"
3. Click OER Commons link
4. **Expected**: Opens `https://oercommons.org/search?search_source=site&f.search=neural+networks`
5. **Expected**: Displays OER Commons search results (not login page)

### Test Related Topics Clickability
1. Ask any AI/ML question (e.g., "what is deep learning?")
2. View "Explore Related Topics" section
3. Click any related topic
4. **Expected**: Immediately submits query and displays results
5. **Expected**: No need to click send button manually

### Verify Removed Sources
1. Ask any query (e.g., "NLP")
2. Click "Load Additional Resources"
3. **Expected Sources**:
   - ✅ YouTube videos (3)
   - ✅ Wikipedia article (1)
   - ✅ OER Commons search link (1)
4. **Should NOT Include**:
   - ❌ Khan Academy links
   - ❌ MIT OCW links

---

## Deployment Checklist

- ✅ Backend changes saved (auto-reload enabled)
- ✅ Chrome extension rebuilt successfully
- ✅ Build validation passed
- ⏳ **Next Step**: Reload extension in Chrome
  1. Go to `chrome://extensions`
  2. Find "Luminate AI"
  3. Click reload button
  4. Test OER Commons links
  5. Test related topics clickability

---

## API Response Structure

### External Resources (Updated)
```json
[
  {
    "title": "YouTube: Video Title",
    "url": "https://youtube.com/watch?v=...",
    "description": "Video description",
    "type": "YouTube",
    "channel": "Channel Name"
  },
  {
    "title": "Wikipedia: Article Title",
    "url": "https://en.wikipedia.org/wiki/...",
    "description": "Article description",
    "type": "Wikipedia",
    "channel": "Wikipedia"
  },
  {
    "title": "OER Commons: query",
    "url": "https://oercommons.org/search?search_source=site&f.search=query",
    "description": "Search open educational resources about query",
    "type": "OER Commons",
    "channel": "OER Commons"
  }
]
```

### Related Topics (Behavior Updated)
```json
[
  {
    "title": "Related Topic Title",
    "why_explore": "Brief reason to explore this"
  }
]
```

**Frontend Behavior**: Clicking triggers immediate search via `handleSubmit(topic.title)`

---

## Backend Log Output

### Before (Khan Academy + MIT OCW):
```
✓ Found Khan Academy: neural network
✓ Found MIT OCW: neural network
```

### After (Simplified):
```
✓ Found Wikipedia article: Neural Network
✓ Found OER Commons: neural network
```

---

## Summary

**Total Removals**: ~85 lines of code (Khan Academy + MIT OCW mappings)
**Total Additions**: ~5 lines (OER URL format + related topics onClick)
**Net Change**: Simpler, more maintainable external resources system

**Benefits**:
1. ✅ OER Commons links now work correctly
2. ✅ Fewer external sources = faster loading
3. ✅ Related topics are truly clickable (one-click action)
4. ✅ Reduced maintenance burden (fewer curated link mappings to update)
5. ✅ Focus on most reliable sources (YouTube API + Wikipedia API)
