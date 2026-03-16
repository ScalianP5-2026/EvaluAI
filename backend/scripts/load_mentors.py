"""Load cleaned mentors CSV data into Supabase using UPSERT."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import pandas as pd

from supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "clean" / "mentors_clean.csv"
BATCH_SIZE = 500


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def _parse_skills(value: Any) -> list[str]:
    raw_text = _clean_text(value)
    if not raw_text:
        return []
    return [skill.strip() for skill in raw_text.split(",") if skill.strip()]


def _build_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    expected_columns = {"mentor_id", "nombre", "department", "especialidades"}
    missing = expected_columns - set(df.columns)
    if missing:
        raise ValueError(f"Missing required mentor columns: {sorted(missing)}")

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        mentor_id = _clean_text(row["mentor_id"])
        if not mentor_id:
            continue

        # CORRECCIÓN AQUÍ: Cambiamos 'or None' por 'or "Sin especificar"' 
        # para respetar la restricción NOT NULL de la base de datos.
        nombre = _clean_text(row.get("nombre", "")) or "Sin especificar"
        department = _clean_text(row.get("department", "")) or "Sin asignar"
        especialidades = _parse_skills(row.get("especialidades", ""))

        records.append(
            {
                "mentor_id": mentor_id,
                "nombre": nombre,
                "department": department,
                "especialidades": especialidades,
            }
        )

    deduped = {record["mentor_id"]: record for record in records}
    return list(deduped.values())


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def main() -> None:
    print("Loading mentors...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Clean mentors file not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    records = _build_records(df)

    if not records:
        logger.warning("No valid mentor rows found. Nothing to upload.")
        return

    supabase = get_supabase_client()

    total_uploaded = 0
    for batch in _chunked(records, BATCH_SIZE):
        supabase.table("mentores").upsert(batch, on_conflict="mentor_id").execute()
        total_uploaded += len(batch)

    print("Mentors uploaded successfully")
    logger.info("Uploaded %s mentor rows using UPSERT.", total_uploaded)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Error loading mentors: %s", exc)
        raise