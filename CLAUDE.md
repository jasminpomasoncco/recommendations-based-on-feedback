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
