"""
E2B Code Executor
Secure Python code execution in sandbox using e2b-code-interpreter SDK v2.x
"""

from typing import Dict, Optional
import logging
import os
from e2b_code_interpreter import Sandbox
from app.config import settings

logger = logging.getLogger(__name__)


class CodeExecutor:
    """Executes Python code in E2B sandbox"""

    def __init__(self):
        # E2B SDK v2.x reads API key from E2B_API_KEY environment variable
        if not settings.e2b_api_key:
            logger.warning("E2B_API_KEY not configured. Code execution will be disabled.")
            self.enabled = False
        else:
            # Set environment variable for E2B SDK
            os.environ["E2B_API_KEY"] = settings.e2b_api_key
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
            # Create sandbox using the class method - SDK reads API key from E2B_API_KEY env var
            sandbox = Sandbox.create()
            
            try:
                # Execute code using run_code method
                execution = sandbox.run_code(code)
                
                # Get output - handle both list and string outputs
                stdout = ""
                stderr = ""
                
                if execution.logs:
                    if hasattr(execution.logs, 'stdout'):
                        stdout_logs = execution.logs.stdout
                        stdout = "".join(stdout_logs) if isinstance(stdout_logs, list) else str(stdout_logs)
                    if hasattr(execution.logs, 'stderr'):
                        stderr_logs = execution.logs.stderr
                        stderr = "".join(stderr_logs) if isinstance(stderr_logs, list) else str(stderr_logs)
                
                # Check for error in execution
                if execution.error:
                    return {
                        "success": False,
                        "error": str(execution.error),
                        "stdout": stdout,
                        "stderr": stderr,
                    }
                
                # Check for generated files/results (images, plots, etc.)
                files = []
                if execution.results:
                    for result in execution.results:
                        if hasattr(result, 'png') and result.png:
                            files.append({"type": "image/png", "data": result.png})
                        elif hasattr(result, 'svg') and result.svg:
                            files.append({"type": "image/svg+xml", "data": result.svg})
                
                return {
                    "success": True,
                    "stdout": stdout,
                    "stderr": stderr,
                    "files": files,
                }
            finally:
                # Close sandbox
                sandbox.kill()
                
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

