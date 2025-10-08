#!/usr/bin/env python3
"""
Quick start script for Luminate AI FastAPI backend
Run from project root: python scripts/start_backend.py
"""
import sys
import subprocess
from pathlib import Path

# Ensure we're in the project root
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

if __name__ == "__main__":
    print("🚀 Starting Luminate AI Backend...")
    print(f"📁 Project root: {project_root}")
    print(f"🌐 Server: http://127.0.0.1:8000")
    print(f"📊 Health: http://127.0.0.1:8000/health")
    print("\n" + "="*60 + "\n")
    
    try:
        subprocess.run([
            sys.executable,
            "-m", "development.backend.fastapi_service.main"
        ], cwd=project_root, check=True)
    except KeyboardInterrupt:
        print("\n\n✨ Server stopped gracefully")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)
