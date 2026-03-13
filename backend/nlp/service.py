from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

# Build dataset path relative to this file to avoid hardcoded absolute paths.
# When running in Docker, __file__ is /app/nlp/service.py, so go up 2 levels to /app
# When running locally, __file__ is /workspaces/EvaluAI/backend/nlp/service.py, so go up 3 levels to /workspaces/EvaluAI/backend
_SERVICE_DIR = Path(__file__).resolve().parent  # /app/nlp or /backend/nlp
_APP_ROOT = _SERVICE_DIR.parent  # /app or /backend

# In Docker: _APP_ROOT is /app, so path is /app/data/processed/survey_nlp_enriched.csv
# Locally: _APP_ROOT is /backend, so path is /backend/data/processed/survey_nlp_enriched.csv
_ENRICHED_DATASET_PATH = _APP_ROOT / "data" / "processed" / "survey_nlp_enriched.csv"

# Keep dataframe and load error cached in memory for fast repeated reads.
_DF_CACHE: pd.DataFrame | None = None
_CACHE_ERROR: str | None = None


def _to_json_ready(value: Any) -> Any:
    """Convert pandas/numpy values to plain Python JSON-serializable values."""
    if isinstance(value, dict):
        return {str(k): _to_json_ready(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_to_json_ready(v) for v in value]
    if isinstance(value, tuple):
        return [_to_json_ready(v) for v in value]
    if pd.isna(value):
        return None
    if hasattr(value, "item"):
        try:
            return value.item()
        except Exception:
            return str(value)
    return value


def _load_dataframe() -> pd.DataFrame | None:
    """Load and cache NLP enriched dataframe, handling missing file gracefully."""
    global _DF_CACHE, _CACHE_ERROR

    if _DF_CACHE is not None:
        return _DF_CACHE

    if not _ENRICHED_DATASET_PATH.exists():
        _CACHE_ERROR = f"NLP dataset not found: {_ENRICHED_DATASET_PATH}"
        return None

    try:
        _DF_CACHE = pd.read_csv(_ENRICHED_DATASET_PATH)
        _CACHE_ERROR = None
        return _DF_CACHE
    except Exception as exc:
        _CACHE_ERROR = f"Failed to read NLP dataset: {exc}"
        return None


def _dataset_error_payload() -> dict[str, Any]:
    """Return a standard error payload when dataset cannot be loaded."""
    return {
        "status": "error",
        "message": _CACHE_ERROR or "NLP dataset is not available.",
        "dataset_path": str(_ENRICHED_DATASET_PATH),
    }


def get_sentiment_summary() -> dict[str, Any]:
    """Return sentiment label distribution and confidence stats."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    if "sentiment_label" not in df.columns:
        return {
            "status": "error",
            "message": "Column 'sentiment_label' not found in dataset.",
        }

    sentiment_counts = df["sentiment_label"].fillna("unknown").astype(str).value_counts(dropna=False)
    sentiment_percentages = (sentiment_counts / len(df)).round(4)

    response: dict[str, Any] = {
        "status": "ok",
        "total_rows": int(len(df)),
        "sentiment_counts": _to_json_ready(sentiment_counts.to_dict()),
        "sentiment_percentages": _to_json_ready(sentiment_percentages.to_dict()),
    }

    if "sentiment_confidence" in df.columns:
        response["sentiment_confidence"] = {
            "mean": _to_json_ready(df["sentiment_confidence"].mean()),
            "median": _to_json_ready(df["sentiment_confidence"].median()),
            "min": _to_json_ready(df["sentiment_confidence"].min()),
            "max": _to_json_ready(df["sentiment_confidence"].max()),
        }

    return response


def get_topic_summary() -> dict[str, Any]:
    """Return topic frequency summary and optional topic-level sentiment breakdown."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    if "topic_id" not in df.columns:
        return {
            "status": "error",
            "message": "Column 'topic_id' not found in dataset.",
        }

    topic_counts = df["topic_id"].value_counts(dropna=False).sort_values(ascending=False)
    topic_percentages = (topic_counts / len(df)).round(4)

    response: dict[str, Any] = {
        "status": "ok",
        "total_rows": int(len(df)),
        "topic_counts": _to_json_ready(topic_counts.to_dict()),
        "topic_percentages": _to_json_ready(topic_percentages.to_dict()),
        "top_10_topics": _to_json_ready(topic_counts.head(10).to_dict()),
    }

    if "sentiment_label" in df.columns:
        topic_sentiment = pd.crosstab(df["topic_id"], df["sentiment_label"]) 
        response["topic_sentiment_crosstab"] = _to_json_ready(topic_sentiment.to_dict())

    return response


def get_npi_distribution() -> dict[str, Any]:
    """Return NLP Psychological Index distribution and descriptive statistics."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    if "nlp_psychological_category" not in df.columns:
        return {
            "status": "error",
            "message": "Column 'nlp_psychological_category' not found in dataset.",
        }

    category_counts = df["nlp_psychological_category"].fillna("unknown").astype(str).value_counts(dropna=False)
    category_percentages = (category_counts / len(df)).round(4)

    response: dict[str, Any] = {
        "status": "ok",
        "total_rows": int(len(df)),
        "npi_category_counts": _to_json_ready(category_counts.to_dict()),
        "npi_category_percentages": _to_json_ready(category_percentages.to_dict()),
    }

    if "nlp_psychological_index" in df.columns:
        response["npi_score_stats"] = {
            "mean": _to_json_ready(df["nlp_psychological_index"].mean()),
            "std": _to_json_ready(df["nlp_psychological_index"].std()),
            "min": _to_json_ready(df["nlp_psychological_index"].min()),
            "max": _to_json_ready(df["nlp_psychological_index"].max()),
            "q25": _to_json_ready(df["nlp_psychological_index"].quantile(0.25)),
            "q50": _to_json_ready(df["nlp_psychological_index"].quantile(0.50)),
            "q75": _to_json_ready(df["nlp_psychological_index"].quantile(0.75)),
        }

    return response


def get_executive_summary() -> dict[str, Any]:
    """Return one executive summary text generated by the NLP pipeline."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    if "executive_summary" not in df.columns:
        return {
            "status": "error",
            "message": "Column 'executive_summary' not found in dataset.",
        }

    non_empty = df["executive_summary"].dropna().astype(str)
    non_empty = non_empty[non_empty.str.strip() != ""]

    if non_empty.empty:
        return {
            "status": "ok",
            "executive_summary": None,
            "message": "No executive summary text available in dataset.",
        }

    return {
        "status": "ok",
        "executive_summary": non_empty.iloc[0],
    }


def get_employee_nlp(employee_id: Any) -> dict[str, Any]:
    """Return NLP details for a single employee by id_empleado."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    if "id_empleado" not in df.columns:
        return {
            "status": "error",
            "message": "Column 'id_empleado' not found in dataset.",
        }

    # Compare as strings to support numeric and string input ids.
    target_id = str(employee_id).strip()
    matches = df[df["id_empleado"].astype(str).str.strip() == target_id]

    if matches.empty:
        return {
            "status": "not_found",
            "employee_id": target_id,
            "message": "Employee not found in NLP dataset.",
        }

    row = matches.iloc[0]

    payload = {
        "employee_id": _to_json_ready(row.get("id_empleado")),
        "sentiment_label": _to_json_ready(row.get("sentiment_label")),
        "sentiment_score": _to_json_ready(row.get("sentiment_score")),
        "sentiment_confidence": _to_json_ready(row.get("sentiment_confidence")),
        "topic_id": _to_json_ready(row.get("topic_id")),
        "topic_probability": _to_json_ready(row.get("topic_probability")),
        "topic_risk_score": _to_json_ready(row.get("topic_risk_score")),
        "autonomy_signal_score": _to_json_ready(row.get("autonomy_signal_score")),
        "nlp_psychological_index": _to_json_ready(row.get("nlp_psychological_index")),
        "nlp_psychological_category": _to_json_ready(row.get("nlp_psychological_category")),
        "full_text": _to_json_ready(row.get("full_text")),
    }

    return {
        "status": "ok",
        "employee": payload,
    }
