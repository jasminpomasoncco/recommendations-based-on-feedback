from __future__ import annotations

import json
import os
import re
from typing import Any

from anthropic import Anthropic


class ClaudeAnalyzer:

    def __init__(self, model: str | None = None) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if isinstance(self.api_key, str):
            self.api_key = self.api_key.strip()

        self.model = os.getenv("ANTHROPIC_MODEL")

        self.client = Anthropic(api_key=self.api_key) if self.api_key else None

    @staticmethod
    def _extract_json(text: str) -> dict[str, Any]:
        cleaned = text.strip()

        def candidate_texts(source: str) -> list[str]:
            candidates = [source]

            fenced_match = re.search(r"```(?:json)?\s*(.*?)\s*```", source, re.DOTALL | re.IGNORECASE)
            if fenced_match:
                candidates.insert(0, fenced_match.group(1).strip())

            # Try to recover the first balanced JSON object/array from noisy text.
            start_positions = [i for i, ch in enumerate(source) if ch in "{"]
            for start in start_positions:
                depth = 0
                in_string = False
                escape = False
                for end in range(start, len(source)):
                    char = source[end]
                    if in_string:
                        if escape:
                            escape = False
                        elif char == "\\":
                            escape = True
                        elif char == '"':
                            in_string = False
                        continue

                    if char == '"':
                        in_string = True
                    elif char == '{':
                        depth += 1
                    elif char == '}':
                        depth -= 1
                        if depth == 0:
                            snippet = source[start : end + 1].strip()
                            if snippet not in candidates:
                                candidates.append(snippet)
                            break

            return candidates

        last_error: Exception | None = None
        for candidate in candidate_texts(cleaned):
            try:
                parsed = json.loads(candidate)
                if isinstance(parsed, dict):
                    return parsed
            except json.JSONDecodeError as exc:
                last_error = exc

        raise ValueError(f"Claude no devolvió un JSON válido. Respuesta recibida: {cleaned[:500]}") from last_error

    def _fallback_analysis(
        self,
        total_comments: int,
        summary_context: str,
        issues_context: str,
        patterns_context: str,
        recommendations_context: str,
        error_detail: str | None = None,
    ) -> dict[str, Any]:
        problema_msg = (
            "No fue posible llamar a Claude porque no está configurada la API key."
            if not self.api_key
            else "No fue posible obtener respuesta válida del servicio de Claude."
        )

        problemas = [problema_msg]
        if error_detail:
            problemas.append(f"Detalle: {error_detail}")

        resumen = (
            "Análisis local generado sin Claude. El archivo contiene "
            f"{total_comments} comentarios. Revisa la configuración de ANTHROPIC_API_KEY y ANTHROPIC_MODEL para obtener un análisis LLM real."
        )

        return {
            "resumen_general": resumen,
            "problemas_detectados": problemas,
            "patrones_o_temas": [
                "El sistema recuperó contexto relevante con RAG, pero usó una respuesta de respaldo.",
            ],
            "recomendaciones_accionables": [
                "Configura ANTHROPIC_API_KEY y vuelve a ejecutar el análisis.",
                "Valida que la variable de entorno ANTHROPIC_MODEL apunte a un modelo válido (consulta la API para listar modelos).",
                "Valida que la columna 'comentarios' exista y tenga datos útiles.",
            ],
        }

    def analyze_comments(
        self,
        total_comments: int,
        summary_context: str,
        issues_context: str,
        patterns_context: str,
        recommendations_context: str,
    ) -> dict[str, Any]:
        if self.client is None:
            return self._fallback_analysis(
                total_comments=total_comments,
                summary_context=summary_context,
                issues_context=issues_context,
                patterns_context=patterns_context,
                recommendations_context=recommendations_context,
            )

        prompt = f"""
Eres un analista senior de experiencia de cliente y negocio.

Objetivo:
Analizar comentarios de clientes y devolver insights accionables en español.

Reglas:
- Responde únicamente con JSON válido.
- No incluyas markdown, ni explicaciones adicionales.
- Sé muy breve: usa frases cortas y directas.
- Limita `resumen_general` a 1-2 frases.
- Limita cada lista a un máximo de 3 elementos.
- No uses bloques de código.
- No agregues texto antes ni después del JSON.
- Usa el contexto recuperado para sintetizar patrones reales.

Debes devolver exactamente estas claves:
- resumen_general: string
- problemas_detectados: array de strings
- patrones_o_temas: array de strings
- recomendaciones_accionables: array de strings

Contexto general:
{summary_context}

Posibles problemas detectados:
{issues_context}

Patrones y temas recurrentes:
{patterns_context}

Contexto para recomendaciones:
{recommendations_context}

Cantidad total de comentarios: {total_comments}
""".strip()

        try:
            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                messages=[{"role": "user", "content": prompt}],
            )

            text = "".join(block.text for block in response.content if hasattr(block, "text"))
            analysis = self._extract_json(text)
        except Exception as exc:  # capture HTTP/auth/model errors from the SDK
            err_str = str(exc)
            return self._fallback_analysis(
                total_comments=total_comments,
                summary_context=summary_context,
                issues_context=issues_context,
                patterns_context=patterns_context,
                recommendations_context=recommendations_context,
                error_detail=err_str,
            )
        required_keys = {
            "resumen_general",
            "problemas_detectados",
            "patrones_o_temas",
            "recomendaciones_accionables",
        }
        missing = required_keys - set(analysis.keys())
        if missing:
            raise ValueError(f"La respuesta de Claude no contiene las claves requeridas: {sorted(missing)}")

        return analysis
