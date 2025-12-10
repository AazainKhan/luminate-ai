"""
Master Data Quality Pipeline

Orchestrates the complete data quality improvement workflow:
1. Validate all external links
2. Analyze images with Ollama vision model
3. Process and enrich all sources
4. Ingest into ChromaDB

Usage:
    python -m app.etl.data_quality_pipeline [--step STEP] [--skip-images]

Steps:
    all - Run complete pipeline (default)
    links - Validate links only
    images - Analyze images only
    process - Process sources only
    ingest - Ingest to ChromaDB only
"""

import argparse
import asyncio
import logging
import sys
from datetime import datetime
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


async def run_link_validation():
    """Run link validation step"""
    logger.info("=" * 60)
    logger.info("STEP 1: Link Validation")
    logger.info("=" * 60)
    
    from app.etl.link_validator import LinkValidator
    
    validator = LinkValidator()
    await validator.run()
    
    return True


async def run_image_analysis(limit: int = None):
    """Run image analysis step"""
    logger.info("=" * 60)
    logger.info("STEP 2: Image Analysis with Ollama")
    logger.info("=" * 60)
    
    from app.etl.image_analyzer import ImageAnalyzer
    
    analyzer = ImageAnalyzer()
    await analyzer.run(limit=limit)
    
    return True


def run_source_processing():
    """Run source processing step"""
    logger.info("=" * 60)
    logger.info("STEP 3: Source Processing & Enrichment")
    logger.info("=" * 60)
    
    from app.etl.source_processor import SourceProcessor
    
    processor = SourceProcessor()
    processor.run()
    
    return True


def run_chromadb_ingestion(clear: bool = False):
    """Run ChromaDB ingestion step"""
    logger.info("=" * 60)
    logger.info("STEP 4: ChromaDB Ingestion")
    logger.info("=" * 60)
    
    from app.etl.ingest_enriched import EnrichedIngester
    
    ingester = EnrichedIngester()
    ingester.run(clear_existing=clear)
    
    return True


async def run_full_pipeline(skip_images: bool = False, image_limit: int = None, clear_db: bool = False):
    """Run the complete data quality pipeline"""
    start_time = datetime.now()
    
    print("\n" + "=" * 70)
    print("  LUMINATE AI - DATA QUALITY IMPROVEMENT PIPELINE")
    print("=" * 70)
    print(f"  Started at: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70 + "\n")
    
    steps_completed = []
    
    try:
        # Step 1: Link Validation
        await run_link_validation()
        steps_completed.append("link_validation")
        
        # Step 2: Image Analysis (optional)
        if not skip_images:
            await run_image_analysis(limit=image_limit)
            steps_completed.append("image_analysis")
        else:
            logger.info("Skipping image analysis (--skip-images flag)")
        
        # Step 3: Source Processing
        run_source_processing()
        steps_completed.append("source_processing")
        
        # Step 4: ChromaDB Ingestion
        run_chromadb_ingestion(clear=clear_db)
        steps_completed.append("chromadb_ingestion")
        
    except Exception as e:
        logger.error(f"Pipeline failed at step: {steps_completed[-1] if steps_completed else 'start'}")
        logger.error(f"Error: {e}")
        raise
    
    end_time = datetime.now()
    duration = end_time - start_time
    
    print("\n" + "=" * 70)
    print("  PIPELINE COMPLETE")
    print("=" * 70)
    print(f"  Steps completed: {', '.join(steps_completed)}")
    print(f"  Duration: {duration}")
    print("=" * 70 + "\n")
    
    return True


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Run data quality improvement pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    # Run complete pipeline
    python -m app.etl.data_quality_pipeline
    
    # Run without image analysis (faster)
    python -m app.etl.data_quality_pipeline --skip-images
    
    # Analyze only 10 images (for testing)
    python -m app.etl.data_quality_pipeline --image-limit 10
    
    # Run specific step only
    python -m app.etl.data_quality_pipeline --step links
    python -m app.etl.data_quality_pipeline --step images
    python -m app.etl.data_quality_pipeline --step process
    python -m app.etl.data_quality_pipeline --step ingest
    
    # Clear and re-ingest
    python -m app.etl.data_quality_pipeline --step ingest --clear
        """
    )
    
    parser.add_argument(
        "--step",
        choices=["all", "links", "images", "process", "ingest"],
        default="all",
        help="Which step to run (default: all)"
    )
    
    parser.add_argument(
        "--skip-images",
        action="store_true",
        help="Skip image analysis step (faster)"
    )
    
    parser.add_argument(
        "--image-limit",
        type=int,
        help="Limit number of images to analyze (for testing)"
    )
    
    parser.add_argument(
        "--clear",
        action="store_true",
        help="Clear existing ChromaDB collections before ingesting"
    )
    
    args = parser.parse_args()
    
    try:
        if args.step == "all":
            asyncio.run(run_full_pipeline(
                skip_images=args.skip_images,
                image_limit=args.image_limit,
                clear_db=args.clear
            ))
        
        elif args.step == "links":
            asyncio.run(run_link_validation())
        
        elif args.step == "images":
            asyncio.run(run_image_analysis(limit=args.image_limit))
        
        elif args.step == "process":
            run_source_processing()
        
        elif args.step == "ingest":
            run_chromadb_ingestion(clear=args.clear)
        
    except KeyboardInterrupt:
        logger.info("Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
