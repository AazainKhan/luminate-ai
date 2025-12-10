"""
Master Data Quality Pipeline

Orchestrates the complete ETL process:
1. Link Validation - Verify external links, convert embed URLs
2. Image Analysis - Analyze course images with Ollama vision
3. Source Processing - Combine and enrich all sources
4. ChromaDB Ingestion - Load into vector database

Usage:
    python -m app.etl.master_pipeline [--skip-images] [--reset-db]
    
Options:
    --skip-images   Skip image analysis (use existing images.json)
    --reset-db      Delete and recreate ChromaDB collections
"""

import argparse
import asyncio
import logging
import subprocess
import sys
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Paths
SCRIPT_DIR = Path(__file__).parent
BACKEND_DIR = SCRIPT_DIR.parent.parent


def run_step(name: str, module: str, args: list = None):
    """Run a pipeline step as a subprocess"""
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print(f"{'='*60}")
    
    cmd = [sys.executable, "-m", module]
    if args:
        cmd.extend(args)
    
    result = subprocess.run(
        cmd,
        cwd=BACKEND_DIR,
        capture_output=False,
    )
    
    if result.returncode != 0:
        logger.error(f"Step '{name}' failed with return code {result.returncode}")
        return False
    
    logger.info(f"Step '{name}' completed successfully")
    return True


async def run_async_step(name: str, module: str, args: list = None):
    """Run an async pipeline step"""
    print(f"\n{'='*60}")
    print(f"STEP: {name}")
    print(f"{'='*60}")
    
    # Import and run the module's async function
    if module == "app.etl.image_analyzer":
        from app.etl.image_analyzer import ImageAnalyzer
        analyzer = ImageAnalyzer()
        limit = None
        if args and "--limit" in args:
            limit_idx = args.index("--limit") + 1
            if limit_idx < len(args):
                limit = int(args[limit_idx])
        await analyzer.run(limit=limit)
        return True
    
    return False


def main():
    parser = argparse.ArgumentParser(description="Run the complete data quality pipeline")
    parser.add_argument("--skip-images", action="store_true", help="Skip image analysis step")
    parser.add_argument("--skip-links", action="store_true", help="Skip link validation step")
    parser.add_argument("--reset-db", action="store_true", help="Reset ChromaDB collections")
    parser.add_argument("--image-limit", type=int, help="Limit number of images to analyze")
    args = parser.parse_args()
    
    print("\n" + "="*60)
    print("LUMINATE AI - MASTER DATA QUALITY PIPELINE")
    print("="*60)
    print("\nThis pipeline will:")
    print("  1. Validate external links (YouTube, Mediasite, etc.)")
    print("  2. Analyze course images with Ollama vision model")
    print("  3. Process and enrich all sources")
    print("  4. Ingest into ChromaDB for RAG retrieval")
    print("\n")
    
    steps_completed = 0
    steps_total = 4
    
    # Step 1: Link Validation
    if not args.skip_links:
        if run_step("Link Validation", "app.etl.link_validator"):
            steps_completed += 1
    else:
        logger.info("Skipping link validation (--skip-links)")
        steps_completed += 1
    
    # Step 2: Image Analysis (async)
    if not args.skip_images:
        try:
            image_args = []
            if args.image_limit:
                image_args = ["--limit", str(args.image_limit)]
            
            asyncio.run(run_async_step("Image Analysis", "app.etl.image_analyzer", image_args))
            steps_completed += 1
        except Exception as e:
            logger.error(f"Image analysis failed: {e}")
            logger.info("Continuing with existing images.json...")
            steps_completed += 1
    else:
        logger.info("Skipping image analysis (--skip-images)")
        steps_completed += 1
    
    # Step 3: Source Processing
    if run_step("Source Processing", "app.etl.source_processor"):
        steps_completed += 1
    
    # Step 4: ChromaDB Ingestion
    ingest_args = []
    if args.reset_db:
        ingest_args.append("--reset")
    
    if run_step("ChromaDB Ingestion", "app.etl.chromadb_ingestor", ingest_args):
        steps_completed += 1
    
    # Summary
    print("\n" + "="*60)
    print("PIPELINE SUMMARY")
    print("="*60)
    print(f"Steps completed: {steps_completed}/{steps_total}")
    
    if steps_completed == steps_total:
        print("\n✅ Pipeline completed successfully!")
        print("\nCollections available in ChromaDB:")
        print("  - comp237_course_materials: Course content with Blackboard links")
        print("  - comp237_media: Mediasite and YouTube videos")
        print("  - comp237_images: Analyzed educational images")
        print("  - comp237_oer: OER supplementary materials")
        print("  - comp237_external: External verified resources")
    else:
        print("\n⚠️ Pipeline completed with some failures")
    
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
