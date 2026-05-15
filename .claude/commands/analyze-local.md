# Analyze the Local Example File

Run a complete analysis using the sample CSV included in the repository.

## Steps

1. Make sure the server is running:
   ```
   py -m uvicorn main:app --reload
   ```

2. Send the request with `file_path` pointing to the sample CSV:
   ```powershell
   Invoke-WebRequest -Uri "http://127.0.0.1:8000/analyze" `
     -Method POST `
     -Body @{ file_path = "example_file/sentiment-analysis.csv"; top_k = "15" }
   ```

   Or with curl:
   ```bash
   curl -X POST http://127.0.0.1:8000/analyze \
     -F "file_path=example_file/sentiment-analysis.csv" \
     -F "top_k=15"
   ```

3. Expected response — a JSON matching the `AnalysisResponse` schema:
   ```json
   {
     "resumen_general": "...",
     "problemas_detectados": ["...", "..."],
     "patrones_o_temas": ["...", "..."],
     "recomendaciones_accionables": ["...", "..."],
     "total_comentarios": 100,
     "comentarios_usados_en_rag": 42
   }
   ```

## Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `file_path` | string | — | Relative or absolute path to the file |
| `top_k` | int | 10 | Comments retrieved per RAG query (min 3) |

## Notes

- The text column must be named: `comentarios`, `comentario`, `comment`, `comments`, or `text`
- Supports `.csv` and `.xlsx`
- If the analysis returns 400, check the file columns using the `feedback-schema` skill
