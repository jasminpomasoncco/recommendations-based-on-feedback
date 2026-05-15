$ErrorActionPreference = 'Stop'

# Runs the MCP server (feedback-pipeline)
# Usage: .\scripts\run_mcp.ps1
#
# Optional env var: FEEDBACK_API_BASE (default: http://127.0.0.1:8000)
# The FastAPI server must be running for call_analyze and save_result to work.

if (Test-Path .\.venv\Scripts\python.exe) {
  .\.venv\Scripts\python.exe mcp_server/server.py
  exit 0
}

py mcp_server/server.py
