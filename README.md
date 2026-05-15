# Customer Feedback Insights

A Python FastAPI service that analyzes customer feedback from Excel or CSV files and turns it into business insights using RAG and Anthropic Claude.

## What it does

Reads feedback, finds recurring themes, detects frequent problems, and automatically generates actionable recommendations.

## Stack

- **FastAPI** — main API
- **sentence-transformers** — embeddings
- **FAISS** — semantic search
- **Claude (Anthropic)** — final LLM analysis

## Project files

- `main.py` — API endpoint
- `rag.py` — embeddings and context retrieval
- `llm.py` — Claude call
- `utils.py` — Excel/CSV reading
- `mcp_server/server.py` — MCP server for Claude Code CLI integration

## Running the server

```bash
pip install -r requirements.txt
uvicorn main:app --reload
# or
py -m uvicorn main:app --reload
```

## Configuration

Create a `.env` file with:

```env
ANTHROPIC_API_KEY=your_key_here
ANTHROPIC_MODEL=claude-opus-4-7
```

## MCP Server (Claude Code CLI)

A custom MCP server is included for use with Claude Code CLI. It exposes 6 tools:

| Tool | Description |
|------|-------------|
| `validate_csv` | Validates a file before sending it to the API |
| `call_analyze` | Calls `POST /analyze` and returns the result |
| `save_result` | Analyzes and persists the result to SQLite |
| `list_analyses` | Lists saved analysis history |
| `get_analysis` | Retrieves a saved analysis by ID |
| `compare_analyses` | Diffs two saved analyses |
 
The FastAPI server must be running for `call_analyze` and `save_result` to work.

## Scripts (Windows)

- Start the server: `./scripts/run_dev.ps1`
- Health check: `./scripts/health_check.ps1`

## Usage

Open http://127.0.0.1:8000/docs and use the `POST /analyze` endpoint to upload your file.

The file must include a text column named `comentarios`, `comment`, `comments`, or `text`.
