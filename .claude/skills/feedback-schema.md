# Feedback Schema — Project Conventions

This skill describes the API input and output schema so that Claude Code
can generate code, tests, and validations correctly without asking questions.

---

## Input File (CSV / Excel)

### Recognized Columns for Feedback Text

The `read_comments_from_excel` function searches for the first column whose normalized name
(lowercase, without quotes, without extra spaces) matches:

| Accepted Name | Example Header in File |
|----------------|------------------------|
| `comentarios` | `Comentarios`, `COMENTARIOS` |
| `comentario` | `Comentario` |
| `comment` | `Comment`, `COMMENT` |
| `comments` | `Comments` |
| `text` | `Text`, `TEXT` |

If no column matches → `ExcelReadError` with message:
> `"The Excel file must contain a text column such as 'comentarios' or 'Text'."`

### File Format

- Valid extensions: `.csv`, `.xlsx`
- Expected CSV encoding: `utf-8-sig` (BOM tolerated)
- Empty rows in the text column are automatically ignored
- CSV files may contain entire lines wrapped in double quotes (automatically unwrapped)

### Additional Columns (Ignored by Current Pipeline)

Other columns such as `date`, `source`, `score`, or `category` may exist — they do not break
processing but are not currently used by the RAG pipeline or the LLM.

---

## AnalysisResponse — Output Schema

```python
class AnalysisResponse(BaseModel):
    resumen_general: str              # Paragraph summarizing the overall feedback status
    problemas_detectados: list[str]  # List of specific issues detected
    patrones_o_temas: list[str]      # Recurring themes or semantic groupings
    recomendaciones_accionables: list[str]  # Prioritized business actions
    total_comentarios: int           # Total valid rows read from the file
    comentarios_usados_en_rag: int   # Unique comments used as RAG context
```

### Valid Response Example

```json
{
  "resumen_general": "Los clientes valoran la rapidez del servicio pero reportan problemas frecuentes con los tiempos de entrega y la atención post-venta.",
  "problemas_detectados": [
    "Retrasos en la entrega de pedidos",
    "Dificultad para contactar soporte post-compra",
    "Productos que no coinciden con la descripción online"
  ],
  "patrones_o_temas": [
    "Logística y envíos (40% de comentarios)",
    "Calidad del producto",
    "Experiencia de compra online"
  ],
  "recomendaciones_accionables": [
    "Implementar notificaciones proactivas de estado de envío",
    "Crear un canal de soporte dedicado post-compra",
    "Revisar las descripciones de producto con mayor tasa de devolución"
  ],
  "total_comentarios": 312,
  "comentarios_usados_en_rag": 38
}
```

---

## Errores HTTP esperados

| Code | Cause |  Typical Message |
|--------|-------|----------------|
| 400 | Archivo sin nombre | `"El archivo no tiene nombre."` |
| 400 | Extensión inválida | `"El archivo debe ser .xlsx o .csv."` |
| 400 | Sin parámetros | `"Debes enviar un archivo en 'file' o una ruta en 'file_path'."` |
| 400 | Sin comentarios | `"No se encontraron comentarios válidos en la columna 'comentarios'."` |
| 400 | Columna no encontrada | `"El archivo Excel debe contener una columna de texto..."` |
| 500 | Error inesperado | `"Error inesperado al analizar comentarios: <detalle>"` |

---

## POST /analyze Endpoint Parameters

| Parameter | Type | Default | Notes |
|-----------|------|---------|-------|
| `file` | UploadFile | None | Multipart file upload |
| `file_path` | str (Form) | None | Ruta local absoluta o relativa |
| `top_k` | int (Form) | 10 | Clampado a [3, len(comments)] |

Only one of `file` or `file_path` is required. If both are provided, file takes priority.
