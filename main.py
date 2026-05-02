from __future__ import annotations

import os
import tempfile
from typing import Optional

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from pydantic import BaseModel, Field

from llm import ClaudeAnalyzer
from rag import CommentRAG
from utils import ExcelReadError, cleanup_file, read_comments_from_excel


load_dotenv()


class AnalysisResponse(BaseModel):
    resumen_general: str = Field(..., description="Resumen general del feedback")
    problemas_detectados: list[str] = Field(..., description="Problemas principales detectados")
    patrones_o_temas: list[str] = Field(..., description="Patrones o temas recurrentes")
    recomendaciones_accionables: list[str] = Field(..., description="Recomendaciones accionables")
    total_comentarios: int = Field(..., description="Cantidad de comentarios analizados")
    comentarios_usados_en_rag: int = Field(..., description="Cantidad de comentarios recuperados para contexto")


app = FastAPI(
    title="Customer Feedback Insights API",
    description="API para analizar comentarios de clientes desde Excel usando RAG + Claude",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

rag_engine = CommentRAG()
llm_analyzer = ClaudeAnalyzer()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_feedback(
    file: Optional[UploadFile] = File(default=None),
    file_path: Optional[str] = Form(default=None),
    top_k: int = Form(default=10),
) -> AnalysisResponse:
    temp_file_path: Optional[str] = None

    try:
        excel_path = ""

        if file is not None:
            if not file.filename:
                raise HTTPException(status_code=400, detail="El archivo no tiene nombre.")

            filename = file.filename.lower()
            if not (filename.endswith(".xlsx") or filename.endswith(".csv")):
                raise HTTPException(status_code=400, detail="El archivo debe ser .xlsx o .csv.")

            suffix = ".csv" if filename.endswith(".csv") else ".xlsx"
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as temp:
                temp.write(await file.read())
                temp_file_path = temp.name

            excel_path = temp_file_path
        elif file_path:
            excel_path = file_path.strip()
        else:
            raise HTTPException(
                status_code=400,
                detail="Debes enviar un archivo en 'file' o una ruta en 'file_path'.",
            )

        comments = read_comments_from_excel(excel_path)

        if not comments:
            raise HTTPException(status_code=400, detail="No se encontraron comentarios válidos en la columna 'comentarios'.")

        top_k = max(3, min(top_k, len(comments)))
        rag_index = rag_engine.build_index(comments)

        summary_comments = rag_engine.retrieve_comments(rag_index, comments, query="Resume la experiencia general de los clientes", top_k=top_k)
        issues_comments = rag_engine.retrieve_comments(rag_index, comments, query="Detecta quejas, problemas y fricciones en la experiencia del cliente", top_k=top_k)
        patterns_comments = rag_engine.retrieve_comments(rag_index, comments, query="Identifica patrones, temas recurrentes y menciones repetidas", top_k=top_k)
        recommendations_comments = rag_engine.retrieve_comments(rag_index, comments, query="Propone acciones concretas y mejoras prioritarias", top_k=top_k)

        summary_context = rag_engine.format_context(summary_comments)
        issues_context = rag_engine.format_context(issues_comments)
        patterns_context = rag_engine.format_context(patterns_comments)
        recommendations_context = rag_engine.format_context(recommendations_comments)

        unique_rag_comments = len({*summary_comments, *issues_comments, *patterns_comments, *recommendations_comments})

        analysis = llm_analyzer.analyze_comments(
            total_comments=len(comments),
            summary_context=summary_context,
            issues_context=issues_context,
            patterns_context=patterns_context,
            recommendations_context=recommendations_context,
        )

        return AnalysisResponse(
            resumen_general=analysis["resumen_general"],
            problemas_detectados=analysis["problemas_detectados"],
            patrones_o_temas=analysis["patrones_o_temas"],
            recomendaciones_accionables=analysis["recomendaciones_accionables"],
            total_comentarios=len(comments),
            comentarios_usados_en_rag=unique_rag_comments,
        )

    except ExcelReadError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except HTTPException:
        raise
    except Exception as exc:  # pragma: no cover - fallback safety
        raise HTTPException(status_code=500, detail=f"Error inesperado al analizar comentarios: {exc}") from exc
    finally:
        if temp_file_path:
            cleanup_file(temp_file_path)


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=True)
