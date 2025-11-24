# Feature 06: Document Processing & Vector Store - Document Processing

## Goal
Process documents (PDF parsing, text extraction, chunking)

## Tasks Completed
- [x] Create DocumentProcessor class
- [x] Implement PDF text extraction (PyPDF2)
- [x] Implement DOCX text extraction (python-docx)
- [x] Implement TXT file reading
- [x] Create text chunking with overlap
- [x] Add content type detection
- [x] Add week number extraction

## Files Created
- `backend/app/etl/document_processor.py` - Document processing utilities

## Features Implemented
1. **Text Extraction**
   - PDF: PyPDF2 page-by-page extraction
   - DOCX: Paragraph extraction
   - TXT: Direct file reading

2. **Text Chunking**
   - Configurable chunk size (default: 1000 chars)
   - Overlap between chunks (default: 200 chars)
   - Sentence boundary awareness
   - Metadata attached to each chunk

3. **Content Classification**
   - Detects: lecture_slide, assignment_instruction, syllabus, assessment, textbook, concept_definition
   - Extracts week number from filenames
   - Preserves file metadata

## Chunking Strategy
- Respects sentence boundaries
- Maintains context with overlap
- Preserves metadata for RAG retrieval

## Next Steps
- Feature 06: Generate embeddings
- Feature 06: Ingest into ChromaDB

