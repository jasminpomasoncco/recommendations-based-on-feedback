from __future__ import annotations

import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx
import pandas as pd
from mcp.server.fastmcp import FastMCP

API_BASE = os.getenv("FEEDBACK_API_BASE", "http://127.0.0.1:8000")
DB_PATH = Path(__file__).parent.parent / "feedback_history.db"

ACCEPTED_COMMENT_COLUMNS = {"comentarios", "comentario", "comment", "comments", "text"}

mcp = FastMCP("feedback-pipeline")

def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("""
        CREATE TABLE IF NOT EXISTS analyses (
            id          TEXT PRIMARY KEY,
            filename    TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            top_k       INTEGER NOT NULL,
            result_json TEXT NOT NULL
        )
    """)
    conn.commit()
    return conn

def _normalize_col(name: object) -> str:
    return str(name).strip().strip('"').strip("'").lower()

@mcp.tool()
def validate_csv(file_path: str) -> dict:

    path = Path(file_path)
    issues: list[str] = []

    if not path.exists():
        return {"valid": False, "issues": [f"File not found: {file_path}"]}

    suffix = path.suffix.lower()
    if suffix not in {".csv", ".xlsx"}:
        return {"valid": False, "issues": [f"Unsupported extension: {suffix}. Use .csv or .xlsx"]}

    try:
        if suffix == ".csv":
            df = pd.read_csv(path, engine="python", skipinitialspace=True)
        else:
            df = pd.read_excel(path)
    except Exception as exc:
        return {"valid": False, "issues": [f"Failed to read file: {exc}"]}

    normalized_cols = {_normalize_col(c): c for c in df.columns}
    comment_col_key = next((k for k in normalized_cols if k in ACCEPTED_COMMENT_COLUMNS), None)
    comment_col = normalized_cols.get(comment_col_key) if comment_col_key else None

    if comment_col is None:
        issues.append(
            f"No text column was found. Columns detected: {list(df.columns)}. "
            f"Accepted names: {sorted(ACCEPTED_COMMENT_COLUMNS)}"
        )
        return {"valid": False, "column_found": None, "total_rows": len(df), "empty_rows": 0, "issues": issues}

    series = df[comment_col].astype(str).str.strip()
    empty_rows = int((series == "" ).sum() + df[comment_col].isna().sum())
    valid_rows = len(df) - empty_rows

    if valid_rows == 0:
        issues.append("The text column exists but has no valid content rows.")

    if valid_rows < 5:
        issues.append(f"Only {valid_rows} valid rows — the analysis may be unrepresentative.")

    return {
        "valid": len(issues) == 0,
        "column_found": str(comment_col),
        "total_rows": len(df),
        "valid_rows": valid_rows,
        "empty_rows": empty_rows,
        "issues": issues,
    }


@mcp.tool()
def call_analyze(file_path: str, top_k: int = 10) -> dict:

    validation = validate_csv(file_path)
    if not validation["valid"]:
        return {"error": "Validation failed", "issues": validation["issues"]}

    top_k = max(3, top_k)
    abs_path = str(Path(file_path).resolve())

    try:
        response = httpx.post(
            f"{API_BASE}/analyze",
            data={"file_path": abs_path, "top_k": str(top_k)},
            timeout=120.0,
        )
        response.raise_for_status()
        return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text
        return {"error": f"HTTP {exc.response.status_code}", "detail": detail}
    except httpx.ConnectError:
        return {
            "error": "Failed to connect to the API",
            "hint": f"Ensure the server is running at {API_BASE}. "
                    "Run: py -m uvicorn main:app --reload",
        }
    except Exception as exc:
        return {"error": str(exc)}


@mcp.tool()
def save_result(file_path: str, top_k: int = 10) -> dict:

    result = call_analyze(file_path, top_k)
    if "error" in result:
        return result

    analysis_id = str(uuid.uuid4())
    filename = Path(file_path).name
    created_at = datetime.now(timezone.utc).isoformat()

    with _get_db() as conn:
        conn.execute(
            "INSERT INTO analyses (id, filename, created_at, top_k, result_json) VALUES (?, ?, ?, ?, ?)",
            (analysis_id, filename, created_at, top_k, json.dumps(result, ensure_ascii=False)),
        )

    return {
        "id": analysis_id,
        "filename": filename,
        "created_at": created_at,
        "total_comments": result.get("total_comentarios"),
    }


@mcp.tool()
def list_analyses(limit: int = 20) -> list[dict]:

    with _get_db() as conn:
        rows = conn.execute(
            "SELECT id, filename, created_at, top_k, result_json FROM analyses ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()

    results = []
    for row in rows:
        result_data = json.loads(row["result_json"])
        results.append({
            "id": row["id"],
            "filename": row["filename"],
            "created_at": row["created_at"],
            "top_k": row["top_k"],
            "total_comentarios": result_data.get("total_comentarios"),
            "comentarios_usados_en_rag": result_data.get("comentarios_usados_en_rag"),
        })

    return results


@mcp.tool()
def get_analysis(analysis_id: str) -> dict:

    with _get_db() as conn:
        row = conn.execute(
            "SELECT * FROM analyses WHERE id = ?", (analysis_id,)
        ).fetchone()

    if row is None:
        return {"error": f"No analysis was found with id: {analysis_id}"}

    result = json.loads(row["result_json"])
    return {
        "id": row["id"],
        "filename": row["filename"],
        "created_at": row["created_at"],
        "top_k": row["top_k"],
        **result,
    }


@mcp.tool()
def compare_analyses(id1: str, id2: str) -> dict:

    a1 = get_analysis(id1)
    a2 = get_analysis(id2)

    if "error" in a1:
        return {"error": f"Analysis 1: {a1['error']}"}
    if "error" in a2:
        return {"error": f"Analysis 2: {a2['error']}"}

    set_problems_1 = set(a1.get("problemas_detectados", []))
    set_problems_2 = set(a2.get("problemas_detectados", []))
    set_recs_1 = set(a1.get("recomendaciones_accionables", []))
    set_recs_2 = set(a2.get("recomendaciones_accionables", []))

    return {
        "analysis_1": {"id": id1, "filename": a1["filename"], "created_at": a1["created_at"]},
        "analysis_2": {"id": id2, "filename": a2["filename"], "created_at": a2["created_at"]},
        "problems": {
            "only_in_1": sorted(set_problems_1 - set_problems_2),
            "only_in_2": sorted(set_problems_2 - set_problems_1),
            "in_both":  sorted(set_problems_1 & set_problems_2),
        },
        "recommendations": {
            "only_in_1": sorted(set_recs_1 - set_recs_2),
            "only_in_2": sorted(set_recs_2 - set_recs_1),
            "in_both":  sorted(set_recs_1 & set_recs_2),
        },
        "summary_1": a1.get("resumen_general", "")[:200],
        "summary_2": a2.get("resumen_general", "")[:200],
    }

if __name__ == "__main__":
    mcp.run(transport="stdio")
