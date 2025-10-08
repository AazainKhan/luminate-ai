# Blackboard Ultra URL Mapping Documentation

## Overview
This document explains how the ingestion pipeline maps local Blackboard export data to live LMS URLs.

## Blackboard Ultra URL Structure

### Base Course URL
```
https://luminate.centennialcollege.ca/ultra/courses/{COURSE_ID}/outline
```
- **Example:** `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline`
- **Purpose:** Course homepage/outline view

### Document/Content URL
```
https://luminate.centennialcollege.ca/ultra/courses/{COURSE_ID}/outline/edit/document/{DOCUMENT_ID}?courseId={COURSE_ID}&view=content&state=view
```
- **Example:** `https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_3960965_1?courseId=_29430_1&view=content&state=view`
- **Purpose:** Direct link to specific course content (documents, pages, modules)

## URL Components Explained

### Path Parameters
1. **`{COURSE_ID}`** (e.g., `_29430_1`)
   - Format: `_{NUMERIC_ID}_1`
   - Blackboard's internal course identifier
   - Found in: Export folder name, imsmanifest.xml
   - Used in: Both path and query string

2. **`{DOCUMENT_ID}`** (e.g., `_3960965_1`, `_800668_1`)
   - Format: `_{NUMERIC_ID}_1`
   - Blackboard's internal content identifier
   - Found in: .dat file names (res*.dat), XML attributes (`id="xxx"`)
   - Each piece of content has a unique document ID

### URL Path Segments
- **`/ultra/courses/`** - Blackboard Ultra base path
- **`/outline/`** - Course outline/content view
- **`/edit/document/`** - Edit/view mode for documents

### Query Parameters
- **`courseId={COURSE_ID}`** - Required for context
- **`view=content`** - Display mode (content view)
- **`state=view`** - Read-only state (vs. edit mode)

## How Our Pipeline Maps URLs

### Extraction Process
```python
def construct_live_url(self, bb_doc_id: str) -> str:
    """Construct live LMS URL from Blackboard document ID."""
    return (
        f"{self.config.base_url}/{self.config.course_id}/outline/edit/"
        f"document/{bb_doc_id}?courseId={self.config.course_id}&view=content&state=view"
    )
```

### Document ID Extraction
1. **From filename:** `res00123.dat` → Extract numeric ID → `_123_1`
2. **From XML:** `<CONTENT id="_800668_1">` → Direct ID
3. **Fallback:** Generate hash-based ID if no BB ID found

### Configuration
```python
Config:
  course_id: "_29430_1"           # From CLI argument
  course_name: "COMP237"          # From CLI argument  
  base_url: "https://luminate.centennialcollege.ca/ultra/courses"
```

## Examples from COMP237 Export

### Example 1: Topic Document
**File:** `res00216.dat`
**Extracted ID:** `_800668_1`
**Live URL:** 
```
https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800668_1?courseId=_29430_1&view=content&state=view
```
**Content:** "Topic 8.2: Linear classifiers"

### Example 2: Module Content
**File:** `res00067.dat`
**Extracted ID:** `_3960965_1` (hypothetical)
**Live URL:**
```
https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_3960965_1?courseId=_29430_1&view=content&state=view
```

## URL Format Validation

### ✅ Correct Format
```
https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800668_1?courseId=_29430_1&view=content&state=view
```

### ❌ Incorrect Formats (NOT used)
```
# Missing outline/edit path
https://luminate.centennialcollege.ca/ultra/courses/_29430_1/document/_800668_1

# Old Blackboard Classic format
https://luminate.centennialcollege.ca/webapps/blackboard/content/listContent.jsp?course_id=_29430_1&content_id=_800668_1

# Missing query parameters
https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800668_1
```

## Content Types with URLs

All extracted content types receive live URL mappings:
- **Documents (.dat):** Course content pages, modules, folders
- **PDFs:** Uploaded PDF files
- **HTML:** Web pages, announcements
- **DOCX:** Word documents
- **PPTX:** PowerPoint presentations
- **Text files:** Syllabi, plain text content

## JSON Output Structure

Each processed document includes:
```json
{
  "course_id": "_29430_1",
  "course_name": "COMP237",
  "bb_doc_id": "_800668_1",
  "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800668_1?courseId=_29430_1&view=content&state=view",
  "chunks": [
    {
      "chunk_id": "_800668_1_chunk_000",
      "live_lms_url": "https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800668_1?courseId=_29430_1&view=content&state=view",
      "content": "..."
    }
  ]
}
```

## Use Cases

### 1. RAG Citation
When a RAG system retrieves a chunk, include the `live_lms_url` in the citation:
```
"Based on the course content about Linear Classifiers [→ View in LMS](https://luminate.centennialcollege.ca/ultra/courses/_29430_1/outline/edit/document/_800668_1?courseId=_29430_1&view=content&state=view)"
```

### 2. ChromaDB Metadata
Store URLs in ChromaDB metadata for easy retrieval:
```python
collection.add(
    documents=[chunk["content"]],
    metadatas=[{
        "source": "COMP237",
        "lms_url": chunk["live_lms_url"],
        "bb_id": "_800668_1"
    }]
)
```

### 3. LangGraph Navigation
Use URLs in graph nodes for clickable navigation:
```python
graph_node = {
    "id": "_800668_1",
    "title": "Topic 8.2: Linear classifiers",
    "url": "https://luminate.centennialcollege.ca/...",
    "relationships": ["NEXT_IN_MODULE", "CONTAINS"]
}
```

## Verification

To verify URLs are working:
1. Extract a sample URL from `comp_237_content/*.json`
2. Log into Blackboard at https://luminate.centennialcollege.ca
3. Navigate to COMP237 course
4. Paste the URL to verify it loads the correct content

## Technical Notes

### Why `/outline/edit/document/`?
- **`/outline`**: Ultra course view (vs. classic view)
- **`/edit`**: Edit context (even when viewing)
- **`/document`**: Document resource type

### Query Parameter Purpose
- **`courseId`**: Required for Blackboard to establish course context
- **`view=content`**: Specifies content viewing mode
- **`state=view`**: Read-only state (students see this; instructors can edit)

### Alternative Paths (Not Used)
- `/cl/outline/items/` - Alternative Ultra path
- `/webapps/blackboard/` - Blackboard Classic paths
- `/learn/api/` - REST API paths

## Statistics from COMP237 Processing

- **Total files processed:** 593
- **Files with BB IDs:** ~580 (98%)
- **Files with live URLs:** ~580 (98%)
- **Chunks with URLs:** 917 (100% of chunks inherit document URL)

## Related Documentation

- **README.md** - Overall pipeline documentation
- **SETUP_GUIDE.md** - Quick start guide
- **PROCESSING_SUMMARY.md** - Actual processing results
- **PROJECT_SUMMARY.md** - Deliverables overview

---

**Last Updated:** October 4, 2025  
**Pipeline Version:** 1.0  
**Course:** COMP237 (_29430_1)
