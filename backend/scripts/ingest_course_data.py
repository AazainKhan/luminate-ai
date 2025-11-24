#!/usr/bin/env python3
"""
Script to ingest COMP 237 course data from raw_data directory into ChromaDB
Run this after starting Docker services to populate the vector store
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.etl.pipeline import run_etl_pipeline
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main():
    """Ingest course data from raw_data directory"""
    # Get project root (assuming script is in backend/scripts/)
    project_root = Path(__file__).parent.parent.parent
    raw_data_dir = project_root / "raw_data"
    
    if not raw_data_dir.exists():
        logger.error(f"raw_data directory not found at: {raw_data_dir}")
        return 1
    
    logger.info(f"Starting ETL pipeline for: {raw_data_dir}")
    
    try:
        # Process the directory
        result = run_etl_pipeline(
            source_path=raw_data_dir,
            course_id="COMP237"
        )
        
        logger.info("✅ ETL Pipeline completed successfully!")
        logger.info(f"📊 Results:")
        logger.info(f"   - Files discovered: {result.get('files_discovered', 0)}")
        logger.info(f"   - Files processed: {result.get('files_processed', 0)}")
        logger.info(f"   - Chunks created: {result.get('chunks_created', 0)}")
        logger.info(f"   - Chunks ingested: {result.get('chunks_ingested', 0)}")
        
        return 0
        
    except Exception as e:
        logger.error(f"❌ ETL Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit(main())

