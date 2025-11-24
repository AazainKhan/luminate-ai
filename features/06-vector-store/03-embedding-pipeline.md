# Feature 06: Document Processing & Vector Store - Embedding Pipeline

## Goal
Generate embeddings and build vector ingestion pipeline

## Tasks Completed
- [x] Create EmbeddingGenerator class
- [x] Integrate Google Gemini embeddings (models/embedding-001)
- [x] Create ETLPipeline orchestrator
- [x] Connect all components (parser → processor → embeddings → ChromaDB)
- [x] Add batch processing support

## Files Created
- `backend/app/rag/embeddings.py` - Embedding generation
- `backend/app/etl/pipeline.py` - ETL orchestration

## Features Implemented
1. **Embedding Generation**
   - Uses Google Gemini embedding-001 model
   - Batch processing for efficiency
   - Error handling

2. **ETL Pipeline**
   - process_blackboard_export() - Full ZIP processing
   - process_directory() - Directory processing (for pre-loaded data)
   - Coordinates: parsing → discovery → processing → embedding → storage

3. **Metadata Schema**
   - source_filename
   - course_id (default: COMP237)
   - content_type
   - week_number
   - file_type
   - chunk_index, chunk_start, chunk_end

## Usage Example
```python
from app.etl.pipeline import run_etl_pipeline
from pathlib import Path

# Process Blackboard export
result = run_etl_pipeline(
    Path("/path/to/export.zip"),
    output_dir=Path("/tmp/extracted"),
    course_id="COMP237"
)

# Process directory (for raw_data)
result = run_etl_pipeline(
    Path("/path/to/raw_data"),
    course_id="COMP237"
)
```

## Next Steps
- Feature 07: Connect RAG to LangGraph agent
- Feature 08: Add admin upload endpoint

