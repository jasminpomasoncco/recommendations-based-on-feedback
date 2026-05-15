# RAG Tuning Guide

Guide for adjusting the RAG pipeline (`rag.py`) without breaking the public API.

---

## top_k Parameter

`top_k` controls how many comments are retrieved **per semantic query**.
The endpoint runs 4 queries (summary, issues, patterns, recommendations),
so the total context sent to Claude can be up to `4 × top_k` unique comments.

| Dataset size | Recommended top_k | Reason |
|-------------|-------------------|--------|
| < 50 rows   | 5                 | Avoid excessive repetition |
| 50–300      | 10 (default)      | Balance quality/tokens |
| 300–1000    | 15–20             | More semantic coverage |
| > 1000      | 20–30             | Consider IVF indexing |

The final value is clamped in `main.py`:
```python
top_k = max(3, min(top_k, len(comments)))
```

---

## Changing the Embeddings Model

The current model is `sentence-transformers/all-MiniLM-L6-v2` (384 dims, ~23MB, fast).

To change it, edit only the default argument in `CommentRAG.__init__`:

```python
# rag.py
class CommentRAG:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
```

### Evaluated Alternative Models

| Model | Dims | Size | Semantic Quality | Latency |
|-------|------|------|-----------------|---------|
| `all-MiniLM-L6-v2` | 384 | 23 MB | Good (limited multilingual) | Very fast |
| `paraphrase-multilingual-MiniLM-L12-v2` | 384 | 118 MB | Better for Spanish | Fast |
| `all-mpnet-base-v2` | 768 | 420 MB | Very good (English) | Medium |
| `intfloat/multilingual-e5-small` | 384 | 118 MB | Very good for Spanish | Fast |

**Recommended for Spanish feedback:** `paraphrase-multilingual-MiniLM-L12-v2`

Safe change — does not affect the public API, only `rag_engine` in `main.py`.

---

## Changing the FAISS Index

### Current: IndexFlatIP (inner product, exact search)

```python
index = faiss.IndexFlatIP(dimension)  # rag.py line ~50
```

- Exact search O(n)
- Suitable up to ~100k vectors
- No training parameters required

### For large datasets (>100k comments): IndexIVFFlat

```python
# Requires prior training
nlist = 100  # number of clusters (sqrt(n) is the rule of thumb)
quantizer = faiss.IndexFlatIP(dimension)
index = faiss.IndexIVFFlat(quantizer, dimension, nlist, faiss.METRIC_INNER_PRODUCT)
index.train(embeddings)  # must be called before add()
index.add(embeddings)
index.nprobe = 10  # clusters to explore during search (more = more accurate, slower)
```

To implement this, `build_index` in `rag.py` needs to receive pre-computed embeddings
(minor refactor — does not change the public signature of `CommentRAG`).

---

## The 4 RAG Queries (defined in main.py)

These queries determine which comments are retrieved for each section of the analysis:

```python
"Resume la experiencia general de los clientes"
"Detecta quejas, problemas y fricciones en la experiencia del cliente"
"Identifica patrones, temas recurrentes y menciones repetidas"
"Propone acciones concretas y mejoras prioritarias"
```

To improve relevance for a specific domain (e.g. e-commerce, healthcare, apps),
add domain context to each query:
```python
"Resume la experiencia general de los clientes de una tienda de ropa online"
```

---

## RAG Quality Diagnostics

If the analysis seems generic or imprecise:

1. Check that `comentarios_usados_en_rag` > 20 (few comments = poor context)
2. Increase `top_k` in the request
3. Verify that the embeddings model handles the feedback language well
4. Print the retrieved contexts before sending them to Claude (temporary debug in `main.py`)
