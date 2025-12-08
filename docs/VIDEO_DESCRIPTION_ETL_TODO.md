# Video Description Metadata - ETL Enhancement

## Problem
Mediasite video sources currently have poor AI-generated descriptions because:
1. The AI cannot read video transcripts
2. Descriptions are generated on-the-fly from chunked text content (not video-specific)
3. This results in generic descriptions like "This source discusses..." instead of meaningful context

## Solution: Add Video Descriptions to ChromaDB Metadata

### Approach
Instead of generating descriptions via API call, **pre-populate descriptions during ETL ingestion** for video resources.

### Implementation Steps

#### 1. Update ETL Pipeline (`backend/app/etl/reingest_from_json.py`)

Add video description extraction when processing embedded resources:

```python
# In process_embedded_resources() function

for item in embedded_resources:
    link_type = item.get("link_type")
    url = item.get("url", "")
    title = item.get("title", "Resource")
    parent_module = item.get("parent_module", "")
    
    # NEW: Extract video description from raw metadata
    video_description = None
    if link_type == "mediasite":
        # Try to extract from Blackboard export metadata
        video_description = item.get("description") or item.get("summary")
        
        # Fallback: Generate from title/module context
        if not video_description:
            video_description = f"Video lecture from {parent_module}: {title}"
    
    metadata = {
        "title": str(title),
        "url": str(url),
        "link_type": str(link_type),
        "parent_module": str(parent_module),
        "description": video_description,  # NEW FIELD
        # ... other fields
    }
```

#### 2. Update RAG Retriever (`backend/app/agent/tools/rag.py`)

Modify `docs_to_sources()` to use metadata description for videos:

```python
def docs_to_sources(self, docs: List[Dict[str, Any]]) -> List[Source]:
    sources = []
    for doc in docs:
        title = doc.get("title", "Document")
        content = doc.get("content", "")
        metadata = doc.get("metadata", {})
        link_type = doc.get("link_type")
        
        # NEW: Prefer metadata description for videos
        if link_type == "mediasite" and metadata.get("description"):
            description = metadata["description"]
        else:
            # Generate from content (existing logic)
            description = self._generate_description_from_content(content)
        
        sources.append(Source(
            title=title,
            description=description,
            # ... other fields
        ))
    return sources
```

#### 3. Blackboard Export Parser Enhancement

Update `backend/app/etl/blackboard_parser.py` to extract video metadata:

```python
def parse_mediasite_link(element):
    """
    Extract video metadata from Blackboard export HTML.
    
    Look for:
    - <a> tag with mediasite URL
    - Adjacent <p> or <div> with description
    - data-description attributes
    """
    title = element.get("title") or element.text.strip()
    url = element.get("href")
    
    # Try to find description
    description = None
    
    # Check for adjacent description text
    next_sibling = element.getnext()
    if next_sibling is not None and next_sibling.tag == "p":
        description = next_sibling.text_content().strip()
    
    # Check for data attributes
    if not description:
        description = element.get("data-description")
    
    return {
        "title": title,
        "url": url,
        "link_type": "mediasite",
        "description": description,  # NEW
    }
```

### Benefits
1. **No API calls needed** - Descriptions stored directly in ChromaDB
2. **Better quality** - Human-curated descriptions from course materials
3. **Consistent** - Same description shown every time
4. **Faster** - No real-time generation delay

### Testing
After implementing:

```bash
# Re-ingest embedded resources with new descriptions
docker exec api_brain python -m app.etl.reingest_from_json \
  --collection embedded_resources \
  --json-file data/raw/embedded_resources.json

# Query a video source to verify description
docker exec api_brain python -c "
from app.agent.tools.rag import get_rag_retriever
r = get_rag_retriever()
docs, _ = r.retrieve('backpropagation', k=5)
for d in docs:
    if d.get('link_type') == 'mediasite':
        print(f'Video: {d[\"title\"]}')
        print(f'Description: {d.get(\"metadata\", {}).get(\"description\")}')
"
```

### Fallback Strategy
If description is missing from metadata:
1. Use title + module context: `"Video lecture from {module}: {title}"`
2. Fall back to existing AI generation (current behavior)

### Related Files
- `backend/app/etl/blackboard_parser.py` - Extract descriptions during parsing
- `backend/app/etl/reingest_from_json.py` - Store descriptions in ChromaDB
- `backend/app/agent/tools/rag.py` - Use stored descriptions
- `backend/app/api/routes/sources.py` - Keep as fallback for non-video sources

### Priority
**Medium** - Current AI generation works, but video descriptions would be significantly better with metadata.

### Estimated Effort
- Parser update: 1-2 hours
- ETL update: 30 minutes  
- RAG update: 30 minutes
- Testing: 1 hour
- **Total: 3-4 hours**
