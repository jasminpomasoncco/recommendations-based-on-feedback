# Customer Feedback Insights

Aplicación en Python con FastAPI para analizar comentarios de clientes desde un archivo Excel o CSV y convertirlos en insights de negocio usando RAG y Claude de Anthropic.

## ¿Para qué sirve?

Sirve para leer feedback, encontrar temas repetidos, detectar problemas frecuentes y generar recomendaciones accionables de forma automática.

## Qué usa

- FastAPI: API principal
- sentence-transformers: embeddings
- FAISS: búsqueda semántica
- Claude: análisis final con LLM

## Archivos principales

- main.py: endpoint de la API
- rag.py: embeddings y recuperación de contexto
- llm.py: llamada a Claude
- utils.py: lectura de Excel/CSV

## Cómo correrlo

```bash
pip install -r requirements.txt
uvicorn main:app --reload
o 
py -m uvicorn main:app --reload
```

## Configuración

Crear un archivo .env con:

```env
ANTHROPIC_API_KEY=tu_clave_aqui
ANTHROPIC_MODEL=claude-opus-4-7
```

## Scripts (Windows)

- Levantar el server: `./scripts/run_dev.ps1`
- Probar healthcheck: `./scripts/health_check.ps1`

## Uso

Abre http://127.0.0.1:8000/docs y usa el endpoint POST /analyze para enviar tu archivo.

El archivo debe incluir una columna de texto como comentarios o Text.
