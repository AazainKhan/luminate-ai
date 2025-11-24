"""
Admin API routes for course management
"""

from fastapi import APIRouter, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse
from typing import Optional
import tempfile
from pathlib import Path
import logging

from app.api.middleware import require_admin
from app.etl.pipeline import ETLPipeline

router = APIRouter(prefix="/api/admin", tags=["admin"])
logger = logging.getLogger(__name__)

# Store ETL job status (in production, use Redis or database)
etl_jobs: dict[str, dict] = {}


@router.post("/upload")
async def upload_course_materials(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    user_info: dict = require_admin,
):
    """
    Upload Blackboard export ZIP or PDF files
    
    Triggers ETL pipeline in background
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file provided")
    
    # Validate file type
    if not (file.filename.endswith('.zip') or file.filename.endswith('.pdf')):
        raise HTTPException(
            status_code=400,
            detail="Only .zip (Blackboard exports) and .pdf files are supported"
        )
    
    # Create temporary file
    suffix = Path(file.filename).suffix
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp_file:
        content = await file.read()
        tmp_file.write(content)
        tmp_path = Path(tmp_file.name)
    
    # Generate job ID
    import uuid
    job_id = str(uuid.uuid4())
    
    # Initialize job status
    etl_jobs[job_id] = {
        "job_id": job_id,
        "filename": file.filename,
        "status": "processing",
        "progress": 0,
        "message": "Starting ETL pipeline...",
        "error": None,
    }
    
    # Run ETL in background
    background_tasks.add_task(
        run_etl_job,
        job_id,
        tmp_path,
        file.filename
    )
    
    return JSONResponse(
        content={
            "job_id": job_id,
            "filename": file.filename,
            "status": "processing",
            "message": "ETL pipeline started",
        }
    )


async def run_etl_job(job_id: str, file_path: Path, filename: str):
    """Run ETL job in background"""
    try:
        etl_jobs[job_id]["progress"] = 10
        etl_jobs[job_id]["message"] = "Parsing Blackboard export..."
        
        pipeline = ETLPipeline()
        
        if file_path.suffix == '.zip':
            # Process Blackboard export
            output_dir = file_path.parent / f"{file_path.stem}_extracted"
            result = pipeline.process_blackboard_export(
                file_path,
                output_dir,
                course_id="COMP237"
            )
        else:
            # Process single PDF (would need to adapt pipeline)
            etl_jobs[job_id]["error"] = "Single PDF processing not yet implemented"
            etl_jobs[job_id]["status"] = "error"
            return
        
        etl_jobs[job_id]["progress"] = 100
        etl_jobs[job_id]["status"] = "completed"
        etl_jobs[job_id]["message"] = f"Successfully processed {result.get('chunks_ingested', 0)} chunks"
        
        # Cleanup
        file_path.unlink(missing_ok=True)
        
    except Exception as e:
        logger.error(f"ETL job {job_id} failed: {e}")
        etl_jobs[job_id]["status"] = "error"
        etl_jobs[job_id]["error"] = str(e)
        etl_jobs[job_id]["message"] = f"Error: {str(e)}"


@router.get("/etl/status/{job_id}")
async def get_etl_status(
    job_id: str,
    user_info: dict = require_admin,
):
    """Get ETL job status"""
    if job_id not in etl_jobs:
        raise HTTPException(status_code=404, detail="Job not found")
    
    return JSONResponse(content=etl_jobs[job_id])


@router.get("/etl/jobs")
async def list_etl_jobs(
    user_info: dict = require_admin,
):
    """List all ETL jobs"""
    return JSONResponse(
        content={
            "jobs": list(etl_jobs.values())
        }
    )


@router.get("/health")
async def get_system_health(
    user_info: dict = require_admin,
):
    """Get system health metrics"""
    try:
        from app.rag.chromadb_client import get_chromadb_client
        
        chromadb = get_chromadb_client()
        collection_info = chromadb.get_collection_info()
        
        return JSONResponse(
            content={
                "chromadb": {
                    "status": "healthy" if "error" not in collection_info else "unhealthy",
                    "document_count": collection_info.get("count", 0),
                },
                "etl_jobs": {
                    "total": len(etl_jobs),
                    "processing": len([j for j in etl_jobs.values() if j["status"] == "processing"]),
                    "completed": len([j for j in etl_jobs.values() if j["status"] == "completed"]),
                    "error": len([j for j in etl_jobs.values() if j["status"] == "error"]),
                },
            }
        )
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return JSONResponse(
            content={
                "chromadb": {"status": "error", "error": str(e)},
                "etl_jobs": {"total": 0},
            },
            status_code=500
        )

