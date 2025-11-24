"""
Code Execution API routes
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import logging

from app.api.middleware import require_student
from app.tools.code_executor import get_code_executor

router = APIRouter(prefix="/api/execute", tags=["execute"])
logger = logging.getLogger(__name__)


class ExecuteRequest(BaseModel):
    code: str
    language: str = "python"
    timeout: Optional[int] = 30


@router.post("/")
async def execute_code(
    request: ExecuteRequest,
    user_info: dict = require_student,
):
    """
    Execute Python code in E2B sandbox
    
    Returns stdout, stderr, and any generated files
    """
    if request.language != "python":
        raise HTTPException(
            status_code=400,
            detail="Only Python code execution is currently supported"
        )
    
    executor = get_code_executor()
    
    try:
        result = await executor.execute_code(
            request.code,
            timeout=request.timeout or 30
        )
        
        return result
    except Exception as e:
        logger.error(f"Error in code execution endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Code execution failed: {str(e)}"
        )

