$ErrorActionPreference = 'Stop'

# Runs the FastAPI dev server
# Usage: .\scripts\run_dev.ps1

if (Test-Path .\.venv\Scripts\python.exe) {
  .\.venv\Scripts\python.exe -m uvicorn main:app --reload
  exit 0
}

py -m uvicorn main:app --reload
