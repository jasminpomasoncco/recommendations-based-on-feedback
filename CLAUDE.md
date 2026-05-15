# Claude instructions (project)

This repository is a Python FastAPI service that analyzes customer feedback from an Excel/CSV file using a lightweight RAG step (SentenceTransformers + FAISS) and then synthesizes business insights with Anthropic Claude.

## Goals

- Keep changes minimal and focused.
- Prefer clear, production-ready code over cleverness.
- Do not introduce new features unless explicitly requested.

## Repo map

- `main.py` — FastAPI app and `/analyze` endpoint.
- `rag.py` — embedding + FAISS index + context formatting.
- `llm.py` — Claude (Anthropic) call.
- `utils.py` — read Excel/CSV and file cleanup helpers.
- `mcp_server/server.py` — MCP server exposing 6 tools for Claude Code CLI: `validate_csv`, `call_analyze`, `save_result`, `list_analyses`, `get_analysis`, `compare_analyses`.
- `feedback_history.db` — SQLite database created automatically by the MCP server (gitignored).

## Setup & run

- Install deps: `pip install -r requirements.txt`
- Run dev server:
  - `uvicorn main:app --reload`
  - or `py -m uvicorn main:app --reload`
- Swagger: http://127.0.0.1:8000/docs

## Environment variables (never commit secrets)

- Local dev uses a `.env` file (already gitignored).
- Required:
  - `ANTHROPIC_API_KEY`
  - `ANTHROPIC_MODEL` (e.g. `claude-opus-4-7`)

Do NOT write secrets (API keys, tokens) into source files, README examples, commits, or logs.

## Coding conventions

- Python: keep typing as used in the repo (type hints + Pydantic models).
- Error handling: raise `HTTPException` for user errors; keep a single fallback `500` for unexpected exceptions.
- Keep Spanish user-facing messages consistent with existing ones.
- Avoid adding new heavy dependencies unless explicitly needed.

## When editing

- Preserve the existing public API (`/health`, `/analyze`) unless asked.
- If you change how inputs are parsed, keep backwards compatibility with:
  - uploading a file via `file`
  - providing a local path via `file_path`
- After code changes, do a quick sanity check by starting the server and hitting `/health`.

## Claude Code CLI (optional)

If you use Claude Code CLI on this repo:

- Keep this file (`CLAUDE.md`) as the source of project rules/context.
- Never paste or store `ANTHROPIC_API_KEY` in prompts, logs, code, or committed files.
- Prefer running the app with `py -m uvicorn main:app --reload` and verifying `GET /health`.
- If your Claude tooling supports permissions/sandboxing, restrict it to the repo folder and avoid any automatic publish/push actions.

### MCP Server

The repo includes a custom MCP server at `mcp_server/server.py`. It is registered in `.mcp.json` (project root) and connects automatically when Claude Code CLI is active.

To run it manually:
```
.venv\Scripts\python.exe mcp_server/server.py
```

The MCP server requires the FastAPI app to be running on `http://127.0.0.1:8000` (or the URL set in `FEEDBACK_API_BASE` env var) for `call_analyze` and `save_result` to work. `validate_csv` and history tools work standalone.

### Starting Claude Code CLI

```powershell
# 1. Activate the venv first
.venv\Scripts\Activate.ps1

# 2. Start the FastAPI server (required for call_analyze / save_result)
py -m uvicorn main:app --reload

# 3. In a new terminal, launch Claude Code
cd "d:\visual_code_proyectos\Proyectos ML\Recommendations_Feedback"
claude

# 4. Verify MCP is connected
/mcp   # should show: feedback-pipeline · ✔ connected · 6 tools
```

### Claude Code CLI commands

Available slash commands (`.claude/commands/`):
- `/analyze-local` — runs `/analyze` with the example CSV file
- `/health-check` — verifies the server is responding
- `/batch-analyze` — processes all CSV/Excel files in a folder

### Skills

Context files loaded automatically by Claude Code (`.claude/skills/`):
- `feedback-schema.md` — accepted CSV columns, `AnalysisResponse` fields, HTTP errors
- `rag-tuning.md` — `top_k` guidelines, alternative embedding models, FAISS index options
