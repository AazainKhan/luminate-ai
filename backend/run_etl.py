import logging
import sys
from pathlib import Path
from app.etl.pipeline import ETLPipeline

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stdout)]
)

logger = logging.getLogger(__name__)

def main():
    zip_path = Path('../raw_data/export.zip')
    output_dir = Path('cleaned_data')
    course_id = 'COMP237'
    
    logger.info(f"Starting ETL pipeline with zip: {zip_path}")
    
    try:
        pipeline = ETLPipeline()
        result = pipeline.process_blackboard_export(zip_path, output_dir, course_id)
        logger.info(f"ETL Pipeline completed: {result}")
    except Exception as e:
        logger.error(f"ETL Pipeline failed: {e}", exc_info=True)

if __name__ == "__main__":
    main()
