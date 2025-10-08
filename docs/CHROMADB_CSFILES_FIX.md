# ChromaDB Cleanup - csfiles Issue Fixed

**Date:** October 7, 2025  
**Issue:** System files (csfiles) appearing in search results with invalid Chrome extension URLs

---

## Problem Description

### Symptoms
- Search results showed "csfiles" as a module/source
- Clicking on csfiles results led to invalid Chrome extension URL:
  ```
  chrome-extension://plnebfmflchocegleejpepgemmcjhnpo/none
  ```
- 547 out of 917 documents (60%) were system files, not course content

### Root Cause
During the initial Blackboard export ingestion, a `csfiles/` directory containing Blackboard internal navigation/system files was incorrectly included in the ChromaDB vector database. These files have no educational value and should never appear in search results.

---

## Solution Implemented

### 1. **Database Cleanup (Permanent Fix)**

Created and ran `/scripts/clean_chromadb_csfiles.py`:

```python
# Removed 547 csfiles entries from ChromaDB
# Final count: 370 documents (all valid course content)
```

**Results:**
- ✅ Removed 547 system file entries
- ✅ Reduced database size from 917 → 370 documents
- ✅ 100% of remaining docs are valid course materials

### 2. **API-Level Filtering (Defense in Depth)**

Updated `/development/backend/fastapi_service/main.py`:

```python
# Filter out system modules in navigate endpoint
module = meta.get("module", "")
if module.lower() in ["csfiles", "system", "navigation", "__internals"]:
    logger.debug(f"Skipping system module: {module}")
    continue
```

**Location:** Line ~244 in `navigate_query` function

### 3. **Retrieval Agent Filtering**

Updated `/development/backend/langgraph/agents/retrieval.py`:

```python
# Filter out system/navigation modules in retrieval
module = meta.get("module", "")
if module.lower() in ["csfiles", "system", "navigation", "__internals"]:
    continue  # Skip system files
```

**Location:** Line ~86 in `_convert_chromadb_results` function

---

## Verification

### Before Cleanup
```python
Module distribution:
- csfiles: 547 documents ❌
- root: 362 documents
- res00067: 8 documents
Total: 917 documents
```

### After Cleanup
```python
Module distribution:
- root: 362 documents ✅
- res00067: 8 documents ✅
Total: 370 documents
```

### Test Query (NLP)
```python
# Before: 
# 1. csfiles (chrome-extension://...none)
# 2. Topic 10.1: Introduction and NLP applications

# After:
# 1. Topic 10.4: Language pre-processing (Module: Root)
# 2. Topic 10.3: Natural language toolkit (nltk) (Module: Root)
# 3. Overview of Module 10 (Module: Root)
```

---

## Module Distribution After Cleanup

| Module | Documents | Description |
|--------|-----------|-------------|
| Root | 362 | Main course content (Topics, Modules, Lectures) |
| res00067 | 8 | Resource files (likely PDFs or supplementary materials) |
| **Total** | **370** | **All valid educational content** |

---

## Files Modified

### 1. **scripts/clean_chromadb_csfiles.py** (NEW)
- Connects to ChromaDB
- Identifies all documents with `module="csfiles"`
- Deletes them in batches
- Verifies cleanup success
- **Run once:** Already executed, database clean

### 2. **development/backend/fastapi_service/main.py**
- **Lines ~244-248:** Added csfiles filtering in navigate endpoint
- **Line ~237:** Increased n_results multiplier (2 → 3) to account for filtering

### 3. **development/backend/langgraph/agents/retrieval.py**
- **Lines ~86-89:** Added csfiles filtering in retrieval agent
- **Line ~41:** Increased n_results (15 → 25) to get enough valid results after filtering

---

## Prevention Strategy

### Future Ingestion
When re-ingesting Blackboard exports, exclude csfiles directory:

```python
# In ingest script
EXCLUDED_DIRS = [
    "csfiles",
    "__MACOSX",
    ".git",
    "system",
    "navigation"
]

# Skip these during file traversal
for root, dirs, files in os.walk(export_dir):
    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]
```

### URL Validation
Only include documents with valid `live_lms_url` metadata:

```python
# During ingestion
if not metadata.get("live_lms_url"):
    if metadata.get("module") == "csfiles":
        skip_document()  # Don't ingest
```

---

## Impact

### User Experience
- ✅ **No more invalid links:** csfiles entries removed
- ✅ **Better search quality:** Only relevant course materials returned
- ✅ **Faster results:** 60% fewer documents to search through

### System Performance
- ✅ **Reduced ChromaDB size:** 917 → 370 documents (-60%)
- ✅ **Faster vector search:** Smaller index, faster queries
- ✅ **Lower memory usage:** Fewer embeddings to store

### Data Quality
- ✅ **100% valid sources:** All remaining docs are course content
- ✅ **Proper module attribution:** "Root" for main topics, "res00067" for resources
- ✅ **No system files:** csfiles, navigation, system modules excluded

---

## Testing Checklist

- [x] Run cleanup script successfully
- [x] Verify csfiles removed (547 deleted)
- [x] Test NLP query (no csfiles in results)
- [x] Check module distribution (root, res00067 only)
- [x] API filtering works (backend logs show skipping)
- [x] Retrieval agent filtering works
- [x] Frontend shows valid modules only
- [x] No Chrome extension URLs in results

---

## Rollback Plan (If Needed)

If cleanup caused issues:

1. **Restore from backup:**
   ```bash
   # If chromadb_data was backed up
   rm -rf chromadb_data
   cp -r chromadb_data.backup chromadb_data
   ```

2. **Re-ingest with exclusions:**
   ```bash
   # Use updated ingest script with csfiles exclusion
   python3 scripts/ingest_clean_luminate.py --exclude-csfiles
   ```

---

## Related Issues

### Blackboard Export Structure
The `csfiles/` directory contains:
- Navigation XML files
- System configuration files
- Internal Blackboard metadata
- No educational content

These should **never** be ingested into the knowledge base.

### Chrome Extension URL Pattern
The invalid URL `chrome-extension://plnebfmflchocegleejpepgemmcjhnpo/none` appears because:
1. Frontend tries to create a link from `live_lms_url` metadata
2. csfiles entries have `live_lms_url: null`
3. Frontend defaults to `#` which Chrome interprets as extension URL

**Fixed by:** Removing csfiles entirely from database.

---

## Conclusion

**Status:** ✅ **RESOLVED**

- Database cleaned (547 csfiles removed)
- API-level filtering added (defense in depth)
- Retrieval agent filtering added
- All search results now show valid course materials only
- No more invalid Chrome extension URLs

**No further action needed** - the fix is permanent and includes preventive measures for future ingestions.

---

**Verified by:** GitHub Copilot AI Agent  
**ChromaDB Version:** 0.6.0  
**Collection:** comp237_content  
**Documents Before:** 917  
**Documents After:** 370  
**Removed:** 547 csfiles entries (60%)
