"""Load cleaned courses CSV data into Supabase using UPSERT."""

from __future__ import annotations

import logging
import uuid
from pathlib import Path
from typing import Any

import pandas as pd

from supabase_client import get_supabase_client

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "clean" / "courses_clean.csv"
BATCH_SIZE = 500


def _clean_text(value: Any) -> str:
    if pd.isna(value):
        return ""
    return str(value).replace("\xa0", " ").strip()


def _to_float_or_none(value: Any) -> float | None:
    if pd.isna(value):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _to_uuid(value: Any, title: str) -> str:
    raw = _clean_text(value)
    if raw:
        try:
            return str(uuid.UUID(raw))
        except ValueError:
            pass
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f"evaluai-course::{title.lower()}"))


def _build_records(df: pd.DataFrame) -> list[dict[str, Any]]:
    title_col = "title" if "title" in df.columns else "course_name"
    department_col = "department" if "department" in df.columns else "category"
    id_col = "id" if "id" in df.columns else "course_id"

    if title_col not in df.columns:
        raise ValueError("Missing title column. Expected 'title' or 'course_name'.")

    records: list[dict[str, Any]] = []
    for _, row in df.iterrows():
        title = _clean_text(row.get(title_col, ""))
        if not title:
            continue

        department = _clean_text(row.get(department_col, "")) or None
        skill_level = _clean_text(row.get("skill_level", "")) or None

        avg_autoeficacia = _to_float_or_none(row.get("avg_autoeficacia_improvement"))
        avg_completion = _to_float_or_none(row.get("avg_completion_rate"))

        records.append(
            {
                "id": _to_uuid(row.get(id_col, ""), title),
                "title": title,
                "department": department,
                "skill_level": skill_level,
                "avg_autoeficacia_improvement": avg_autoeficacia,
                "avg_completion_rate": avg_completion,
            }
        )

    deduped = {record["title"]: record for record in records}
    return list(deduped.values())


def _chunked(items: list[dict[str, Any]], size: int) -> list[list[dict[str, Any]]]:
    return [items[index : index + size] for index in range(0, len(items), size)]


def main() -> None:
    print("Loading courses...")

    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Clean courses file not found: {DATA_PATH}")

    df = pd.read_csv(DATA_PATH)
    records = _build_records(df)

    if not records:
        logger.warning("No valid course rows found. Nothing to upload.")
        return

    supabase = get_supabase_client()

    total_uploaded = 0
    for batch in _chunked(records, BATCH_SIZE):
        supabase.table("courses").upsert(batch, on_conflict="title").execute()
        total_uploaded += len(batch)

    print("Courses uploaded successfully")
    logger.info("Uploaded %s course rows using UPSERT.", total_uploaded)


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        logger.exception("Error loading courses: %s", exc)
        raise
