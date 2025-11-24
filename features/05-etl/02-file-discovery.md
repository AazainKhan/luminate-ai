# Feature 05: Blackboard ETL Pipeline - File Discovery

## Goal
Extract PDFs, documents, and course materials from Blackboard ZIP

## Tasks Completed
- [x] Create FileDiscovery class
- [x] Implement file discovery with glob patterns
- [x] Categorize files by type
- [x] Filter system files
- [x] Provide convenience methods (find_pdfs, find_documents, etc.)

## Usage Example
```python
from app.etl.file_discovery import discover_course_files
from pathlib import Path

# Discover files in extracted directory
files = discover_course_files(Path("/path/to/extracted"))

# Access categorized files
pdfs = files["pdfs"]
documents = files["documents"]
images = files["images"]
```

## Integration with Parser
The file discovery works with the BlackboardParser:
1. Parser extracts ZIP to directory
2. FileDiscovery scans extracted directory
3. Files are categorized and ready for processing

## Next Steps
- Feature 06: Process discovered files (PDF parsing, text extraction)
- Feature 06: Generate embeddings and store in ChromaDB

