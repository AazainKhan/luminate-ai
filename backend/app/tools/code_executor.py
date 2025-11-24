"""
E2B Code Executor
Secure Python code execution in sandbox
"""

from typing import Dict, Optional
import logging
from e2b import Sandbox
from app.config import settings

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Executes Python code in E2B sandbox"""

    def __init__(self):
        if not settings.e2b_api_key:
            logger.warning("E2B_API_KEY not configured. Code execution will be disabled.")
            self.enabled = False
        else:
            self.enabled = True

    async def execute_code(
        self,
        code: str,
        timeout: int = 30
    ) -> Dict[str, any]:
        """
        Execute Python code in E2B sandbox
        
        Args:
            code: Python code to execute
            timeout: Execution timeout in seconds
            
        Returns:
            Dictionary with stdout, stderr, and any generated files
        """
        if not self.enabled:
            return {
                "success": False,
                "error": "E2B code execution is not configured",
                "stdout": "",
                "stderr": "",
            }

        try:
            # Create sandbox
            sandbox = Sandbox(api_key=settings.e2b_api_key)
            
            try:
                # Execute code
                execution = sandbox.run_code(code, timeout=timeout)
                
                # Get output
                stdout = execution.logs.stdout if hasattr(execution.logs, 'stdout') else ""
                stderr = execution.logs.stderr if hasattr(execution.logs, 'stderr') else ""
                
                # Check for generated files (images, plots, etc.)
                files = []
                # E2B sandbox can list files if needed
                
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr,
                    "files": files,
                }
            finally:
                # Close sandbox
                sandbox.close()
                
        except Exception as e:
            logger.error(f"Error executing code: {e}")
            return {
                "success": False,
                "error": str(e),
                "stdout": "",
                "stderr": "",
            }


# Global instance
_code_executor: Optional[CodeExecutor] = None


def get_code_executor() -> CodeExecutor:
    """Get or create code executor instance"""
    global _code_executor
    if _code_executor is None:
        _code_executor = CodeExecutor()
    return _code_executor

