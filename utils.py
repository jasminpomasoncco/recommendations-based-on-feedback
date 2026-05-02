from __future__ import annotations

import csv
from io import StringIO
from pathlib import Path

import pandas as pd


class ExcelReadError(Exception):
    pass


def _normalize_column_name(name: object) -> str:
    return str(name).strip().strip('"').strip("'").lower()


def _read_csv_robust(path: Path) -> pd.DataFrame:
    """Read CSV files that may have entire lines wrapped in quotes.

    Some exports produce lines like:
    "Text, Sentiment, Source"
    "\"I love it!\", Positive, Twitter"

    Pandas can interpret those as a single column, so we normalize the raw
    text and parse it manually as a fallback.
    """

    try:
        df = pd.read_csv(path, engine="python", skipinitialspace=True)
    except Exception:
        df = pd.DataFrame()

    preferred_columns = ["comentarios", "comentario", "comment", "comments", "text"]
    normalized_columns = [_normalize_column_name(col) for col in df.columns]
    if any(col in preferred_columns for col in normalized_columns):
        df.columns = [str(col).strip().strip('"').strip("'") for col in df.columns]
        return df

    raw_lines = path.read_text(encoding="utf-8-sig", errors="ignore").splitlines()
    cleaned_lines: list[str] = []
    for line in raw_lines:
        stripped = line.strip()
        if len(stripped) >= 2 and stripped[0] == '"' and stripped[-1] == '"':
            stripped = stripped[1:-1]
        cleaned_lines.append(stripped)

    reader = csv.reader(StringIO("\n".join(cleaned_lines)), skipinitialspace=True)
    rows = list(reader)
    if not rows:
        raise ExcelReadError("El CSV está vacío o no se pudo interpretar.")

    header = [cell.strip().strip('"').strip("'") for cell in rows[0]]
    data_rows = rows[1:]
    if not header:
        raise ExcelReadError("No se pudo leer el encabezado del CSV.")

    max_len = max(len(header), *(len(row) for row in data_rows)) if data_rows else len(header)
    if len(header) < max_len:
        header.extend([f"columna_{i}" for i in range(len(header) + 1, max_len + 1)])

    normalized_rows: list[list[str]] = []
    for row in data_rows:
        values = [cell.strip().strip('"').strip("'") for cell in row]
        if len(values) < len(header):
            values.extend([""] * (len(header) - len(values)))
        normalized_rows.append(values[: len(header)])

    return pd.DataFrame(normalized_rows, columns=header[: len(normalized_rows[0]) if normalized_rows else len(header)])


def read_comments_from_excel(file_path: str) -> list[str]:
    path = Path(file_path)
    if not path.exists():
        raise ExcelReadError(f"El archivo no existe: {file_path}")

    suffix = path.suffix.lower()
    if suffix not in {".xlsx", ".csv"}:
        raise ExcelReadError("El archivo debe tener extensión .xlsx o .csv")

    try:
        if suffix == ".csv":
            df = _read_csv_robust(path)
        else:
            df = pd.read_excel(path)
    except Exception as exc:
        raise ExcelReadError(f"No se pudo leer el archivo: {exc}") from exc

    preferred_columns = ["comentarios", "comentario", "comment", "comments", "text"]
    comment_column = next(
        (
            col
            for col in df.columns
            if _normalize_column_name(col) in preferred_columns
        ),
        None,
    )

    if comment_column is None:
        raise ExcelReadError(
            "El archivo Excel debe contener una columna de texto como 'comentarios' o 'Text'."
        )

    comments = (
        df[comment_column]
        .dropna()
        .astype(str)
        .map(str.strip)
        .tolist()
    )

    return [comment for comment in comments if comment]


def cleanup_file(file_path: str) -> None:
    path = Path(file_path)
    if path.exists():
        try:
            path.unlink()
        except OSError:
            pass
