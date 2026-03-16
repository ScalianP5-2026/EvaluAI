"""Load cleaned survey answers CSV data into Supabase using UPSERT."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

CLEAN_DIR = Path(__file__).resolve().parents[1] / "data" / "clean"
CANDIDATE_FILES = [
    CLEAN_DIR / "survey_answers_clean.csv",
    CLEAN_DIR / "survey_clean.csv",
]
BATCH_SIZE = 500


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def _to_int_or_none(value: Any) -> int | None:
    if pd.isna(value):
        return None
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _to_bool_or_none(value: Any) -> bool | None:
    if pd.isna(value):
        return None

    if isinstance(value, bool):
        return value

    if isinstance(value, (int, float)):
        return bool(int(value))

    text = _clean_text(value).lower()
    if text in {"1", "true", "t", "yes", "y", "si", "sí"}:
        return True
    if text in {"0", "false", "f", "no", "n"}:
        return False
    return None


def _resolve_data_path() -> Path:
    for file_path in CANDIDATE_FILES:
        if file_path.exists():
            return file_path
    raise FileNotFoundError(
        "No clean survey answers file found. Expected one of: "
        f"{', '.join(str(path) for path in CANDIDATE_FILES)}"
    )


def _build_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    employee_col = "employee_id" if "employee_id" in df.columns else "id_empleado"
    freq_col = (
        "ai_usage_frequency"
        if "ai_usage_frequency" in df.columns
        else "frecuencia_uso_ia"
    )
    chatgpt_col = "uses_chatgpt" if "uses_chatgpt" in df.columns else "usa_chatgpt"

    if employee_col not in df.columns:
        raise ValueError("Missing employee id column. Expected 'employee_id' or 'id_empleado'.")

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        employee_id = _clean_text(row.get(employee_col, ""))
        if not employee_id:
            continue

        records.append(
            {
                "employee_id": employee_id,
                "ai_usage_frequency": _to_int_or_none(row.get(freq_col)),
                "uses_chatgpt": _to_bool_or_none(row.get(chatgpt_col)),
            }
        )

    deduped = {record["employee_id"]: record for record in records}
    return list(deduped.values())


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def main() -> None:
    print("Loading survey answers...")

    data_path = _resolve_data_path()
    df = pd.read_csv(data_path)
    records = _build_records(df)

    if not records:
        logger.warning("No valid survey answer rows found. Nothing to upload.")
        return

    supabase = get_supabase_client()

    total_uploaded = 0
    for batch in _chunked(records, BATCH_SIZE):
        supabase.table("survey_answers").upsert(batch, on_conflict="employee_id").execute()
        total_uploaded += len(batch)

    print("Survey answers uploaded successfully")
    logger.info("Uploaded %s survey answer rows using UPSERT.", total_uploaded)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Error loading survey answers: %s", exc)
        raise
