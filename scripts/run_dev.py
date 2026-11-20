#!/usr/bin/env python3
"""
scripts/run_dev.py

Convenience development script to start the AgenticDev FastAPI backend
with hot-reload and environment checking.
"""

import os
import subprocess
import sys

def main():
    root_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    backend_dir = os.path.join(root_dir, "backend")
    
    print("Starting AgenticDev Backend Server on http://localhost:8000 ...")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "main:app",
        "--app-dir",
        backend_dir,
        "--reload",
        "--port",
        "8000"
    ]
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nBackend server stopped.")

if __name__ == "__main__":
    main()

