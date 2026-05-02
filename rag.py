from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer


@dataclass
class RAGResult:
    indices: list[int]
    scores: list[float]
    contexts: list[str]


class CommentRAG:
    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2") -> None:
        self.model_name = model_name
        self.model = SentenceTransformer(model_name)

    @staticmethod
    def _normalize_texts(texts: Iterable[str]) -> list[str]:
        normalized = []
        for text in texts:
            if text is None:
                continue
            value = str(text).strip()
            if value:
                normalized.append(value)
        return normalized

    def embed_texts(self, texts: list[str]) -> np.ndarray:
        normalized_texts = self._normalize_texts(texts)
        if not normalized_texts:
            raise ValueError("No hay textos válidos para generar embeddings.")

        embeddings = self.model.encode(
            normalized_texts,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        )
        return np.asarray(embeddings, dtype=np.float32)

    def build_index(self, texts: list[str]) -> faiss.Index:
        embeddings = self.embed_texts(texts)
        dimension = embeddings.shape[1]
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        return index

    def retrieve_comments(self, index: faiss.Index, texts: list[str], query: str, top_k: int = 10) -> list[str]:
        if not query.strip():
            raise ValueError("La query de búsqueda no puede estar vacía.")

        normalized_texts = self._normalize_texts(texts)
        if not normalized_texts:
            raise ValueError("No hay textos válidos para recuperar contexto.")

        query_embedding = self.model.encode(
            [query],
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=False,
        ).astype(np.float32)

        limit = min(top_k, len(normalized_texts))
        scores, indices = index.search(query_embedding, limit)

        contexts = []
        for idx in indices[0]:
            if idx == -1:
                continue
            contexts.append(normalized_texts[idx])

        if not contexts:
            raise ValueError("No se pudieron recuperar comentarios relevantes.")

        unique_contexts = []
        seen = set()
        for context in contexts:
            if context not in seen:
                seen.add(context)
                unique_contexts.append(context)

        return unique_contexts

    @staticmethod
    def format_context(comments: list[str]) -> str:
        return "\n".join(f"- {comment}" for comment in comments)
