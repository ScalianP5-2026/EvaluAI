from __future__ import annotations

import asyncio
import logging
import textwrap
from pathlib import Path
from typing import Any

import pandas as pd

try:  # pragma: no cover - import path differs between runtimes
    from backend.app.chatbot.gemini_client import GeminiChatClient
except ImportError:  # pragma: no cover
    try:
        from app.chatbot.gemini_client import GeminiChatClient  # type: ignore
    except ImportError:  # pragma: no cover
        GeminiChatClient = None  # type: ignore


logger = logging.getLogger(__name__)

# Build dataset path relative to this file to avoid hardcoded absolute paths.
# When running in Docker, __file__ is /app/nlp/service.py, so go up 2 levels to /app
# When running locally, __file__ is /workspaces/EvaluAI/backend/nlp/service.py, so go up 3 levels to /workspaces/EvaluAI/backend
_SERVICE_DIR = Path(__file__).resolve().parent  # /app/nlp or /backend/nlp
_APP_ROOT = _SERVICE_DIR.parent  # /app or /backend

# In Docker: _APP_ROOT is /app, so path is /app/data/processed/survey_nlp_enriched.csv
# Locally: _APP_ROOT is /backend, so path is /backend/data/processed/survey_nlp_enriched.csv
_ENRICHED_DATASET_PATH = _APP_ROOT / "data" / "processed" / "survey_nlp_enriched.csv"
_ENGINEERED_DATASET_PATH = _APP_ROOT / "data" / "processed" / "survey_engineered.csv"

# Keep dataframe and load error cached in memory for fast repeated reads.
_DF_CACHE: pd.DataFrame | None = None
_CACHE_ERROR: str | None = None
_ENGINEERED_DF_CACHE: pd.DataFrame | None = None
_ENGINEERED_CACHE_ERROR: str | None = None
_EXECUTIVE_CACHE: dict[str, str | None] = {"en": None, "es": None}
_LLM_CLIENT: GeminiChatClient | None = None
_DEFAULT_LANGUAGE = "en"
_SUPPORTED_LANGS = {"en": "English", "es": "Spanish"}


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


def _engineered_dataset_error_payload() -> dict[str, Any]:
    """Return error payload when engineered dataset cannot be loaded."""
    return {
        "status": "error",
        "message": _ENGINEERED_CACHE_ERROR
        or "Engineered dataset is not available.",
        "dataset_path": str(_ENGINEERED_DATASET_PATH),
    }


def _load_engineered_dataframe() -> pd.DataFrame | None:
    """Load engineered dataset with caching and graceful errors."""
    global _ENGINEERED_DF_CACHE, _ENGINEERED_CACHE_ERROR

    if _ENGINEERED_DF_CACHE is not None:
        return _ENGINEERED_DF_CACHE

    if not _ENGINEERED_DATASET_PATH.exists():
        _ENGINEERED_CACHE_ERROR = (
            f"Engineered dataset not found: {_ENGINEERED_DATASET_PATH}"
        )
        return None

    try:
        _ENGINEERED_DF_CACHE = pd.read_csv(_ENGINEERED_DATASET_PATH)
        _ENGINEERED_CACHE_ERROR = None
        return _ENGINEERED_DF_CACHE
    except Exception as exc:
        _ENGINEERED_CACHE_ERROR = f"Failed to read engineered dataset: {exc}"
        return None


def _normalize_language(lang: str | None) -> str:
    """Normalize requested language to supported set."""
    if not lang:
        return _DEFAULT_LANGUAGE
    lang_code = lang.lower()
    return lang_code if lang_code in _EXECUTIVE_CACHE else _DEFAULT_LANGUAGE


def _get_llm_client() -> GeminiChatClient | None:
    """Lazy-load Gemini client, logging failures but keeping service alive."""
    global _LLM_CLIENT

    if _LLM_CLIENT is not None:
        return _LLM_CLIENT

    if GeminiChatClient is None:
        logger.warning(
            "GeminiChatClient not available; executive summaries will use fallback text."
        )
        return None

    try:
        _LLM_CLIENT = GeminiChatClient()
    except Exception as exc:  # pragma: no cover - depends on env secrets
        logger.warning("Failed to initialize GeminiChatClient: %s", exc)
        _LLM_CLIENT = None

    return _LLM_CLIENT


def call_llm(prompt: str) -> str | None:
    """Send prompt to LLM, returning None when unavailable or failing."""
    client = _get_llm_client()
    if client is None or not prompt.strip():
        return None

    async def _invoke() -> str:
        return await client.query(prompt)

    try:
        return asyncio.run(_invoke())
    except RuntimeError as exc:
        # Happens inside notebook contexts with running loop; fall back to manual loop.
        if "asyncio.run() cannot be called" in str(exc):
            loop = asyncio.new_event_loop()
            try:
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(_invoke())
            finally:
                asyncio.set_event_loop(None)
                loop.close()
        logger.warning("LLM execution failed: %s", exc)
    except Exception as exc:  # pragma: no cover - external API failures
        logger.warning("LLM execution failed: %s", exc)

    return None


def _top_entry(distribution: dict[str, Any]) -> tuple[str, float]:
    if not distribution:
        return "unknown", 0.0
    key, value = max(distribution.items(), key=lambda item: item[1])
    try:
        numeric_value = float(value)
    except (TypeError, ValueError):
        numeric_value = 0.0
    return str(key), numeric_value


def _format_percentage(value: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round((value / total) * 100, 1)


def _percent_of_category(df: pd.DataFrame, column: str, match_value: str) -> float:
    if column not in df.columns or df.empty:
        return 0.0
    series = df[column].fillna("" ).astype(str).str.lower()
    target = str(match_value).lower()
    percent = (series == target).sum() / len(df) * 100
    return round(float(percent), 2)


def _safe_numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series(dtype=float)
    return pd.to_numeric(df[column], errors="coerce")


def _normalized_mean(series: pd.Series) -> float:
    numeric = series.dropna()
    if numeric.empty:
        return 0.0
    min_val = float(numeric.min())
    max_val = float(numeric.max())
    if max_val - min_val <= 0:
        return 0.0
    normalized = (numeric - min_val) / (max_val - min_val)
    return float(normalized.mean())


def _classify_topic_risk(score: float) -> str:
    if score is None:
        return "low"
    if score > 0.66:
        return "high"
    if score >= 0.33:
        return "medium"
    return "low"


def _determine_top_risk_topic(df: pd.DataFrame) -> str | None:
    if df.empty or "topic_id" not in df.columns or "topic_risk_score" not in df.columns:
        return None

    prepared = df.dropna(subset=["topic_id", "topic_risk_score"])
    if prepared.empty:
        return None

    total = len(prepared)
    grouped = prepared.groupby("topic_id")
    weighted_scores = grouped["topic_risk_score"].mean() * (grouped.size() / total)
    if weighted_scores.empty:
        return None
    try:
        best_topic = weighted_scores.idxmax()
    except Exception:
        return None
    return str(best_topic)


def _build_top_topics_table(df: pd.DataFrame) -> list[dict[str, Any]]:
    if df.empty or "topic_id" not in df.columns:
        return []

    topic_counts = df["topic_id"].value_counts(dropna=False)
    total_mentions = float(topic_counts.sum() or len(df) or 1)

    avg_risk = (
        df.groupby("topic_id")["topic_risk_score"].mean()
        if "topic_risk_score" in df.columns
        else pd.Series(dtype=float)
    )

    rows: list[dict[str, Any]] = []
    for topic_id, count in topic_counts.head(5).items():
        avg_value = float(avg_risk.get(topic_id)) if topic_id in avg_risk else None
        risk_level = _classify_topic_risk(avg_value or 0.0)
        percent = round(float(count) / total_mentions * 100, 2)
        rows.append(
            {
                "topic": str(topic_id),
                "percent": percent,
                "avg_topic_risk_score": round(avg_value, 3) if avg_value is not None else None,
                "risk_level": risk_level,
                "implication": _TOPIC_IMPLICATIONS.get(risk_level, _TOPIC_IMPLICATIONS["low"]),
            }
        )

    return rows


_SENTIMENT_TERMS = {
    "positive": {"en": "positive sentiment", "es": "sentimiento positivo"},
    "neutral": {"en": "neutral sentiment", "es": "sentimiento neutral"},
    "negative": {"en": "negative sentiment", "es": "sentimiento negativo"},
}

_RISK_TERMS = {
    "high_risk": {"en": "high dependency risk", "es": "riesgo alto de dependencia"},
    "medium_risk": {"en": "medium dependency risk", "es": "riesgo medio de dependencia"},
    "low_risk": {"en": "low dependency risk", "es": "riesgo bajo de dependencia"},
}

_TOPIC_IMPLICATIONS = {
    "high": "High dependency or autonomy erosion risk",
    "medium": "Moderate behavioral impact",
    "low": "Low strategic concern",
}


def _localize_term(mapping: dict[str, dict[str, str]], label: str, lang: str) -> str:
    normalized = str(label).strip().lower()
    if normalized in mapping:
        entry = mapping[normalized]
        return entry.get(lang, entry.get("en", normalized))
    readable = normalized.replace("_", " ")
    if lang == "es":
        return readable
    return readable


def _format_topic_label(topic_id: str, lang: str) -> str:
    prefix = "Tema" if lang == "es" else "Topic"
    try:
        numeric = int(str(topic_id).strip())
        index = numeric + 1 if numeric >= 0 else numeric
        return f"{prefix} {index}"
    except (TypeError, ValueError):
        safe_value = str(topic_id).strip() or "?"
        return f"{prefix} {safe_value}"


def _build_topic_sentence(topic_distribution: dict[str, Any], lang: str) -> str:
    if not topic_distribution:
        return "No dominant topics" if lang == "en" else "Sin temas dominantes"

    top_items = list(topic_distribution.items())[:3]
    fragments: list[str] = []
    for topic_id, count in top_items:
        try:
            safe_count = int(count)
        except (TypeError, ValueError):
            safe_count = 0
        fragments.append(f"{_format_topic_label(topic_id, lang)} ({safe_count})")

    prefix = "Top themes" if lang == "en" else "Temas principales"
    return f"{prefix}: {', '.join(fragments)}"


def _build_fallback_summary(
    lang: str,
    sentiment_distribution: dict[str, Any],
    topic_distribution: dict[str, Any],
    npi_distribution: dict[str, Any],
) -> str:
    sentiment_label, sentiment_value = _top_entry(sentiment_distribution)
    topic_sentence = _build_topic_sentence(topic_distribution, lang)
    risk_label, risk_value = _top_entry(npi_distribution)

    total_sentiment = sum(float(v or 0) for v in sentiment_distribution.values()) or 1.0
    total_risk = sum(float(v or 0) for v in npi_distribution.values()) or 1.0

    sentiment_percent = _format_percentage(sentiment_value, total_sentiment)
    risk_percent = _format_percentage(risk_value, total_risk)

    if lang == "es":
        lines = [
            "Insight Ejecutivo NLP (fallback)",
            f"- Sentimiento dominante: {_localize_term(_SENTIMENT_TERMS, sentiment_label, lang)} ({sentiment_percent}%).",
            f"- {topic_sentence}.",
            f"- Riesgo de autonomía/dependencia IA más frecuente: {_localize_term(_RISK_TERMS, risk_label, lang)} ({risk_percent}%).",
            "- Acción sugerida: reforzar la alfabetización en IA, supervisar equipos con riesgo alto y preservar la autonomía de decisiones.",
        ]
    else:
        lines = [
            "Executive NLP Insight (fallback)",
            f"- Predominant sentiment: {_localize_term(_SENTIMENT_TERMS, sentiment_label, lang)} ({sentiment_percent}%).",
            f"- {topic_sentence}.",
            f"- AI autonomy/dependency risk trend: {_localize_term(_RISK_TERMS, risk_label, lang)} ({risk_percent}%).",
            "- Recommended action: reinforce AI literacy coaching, monitor high-risk cohorts, and protect human autonomy checkpoints.",
        ]

    return "\n".join(lines)


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
    """Return AI Autonomy & Dependency Index distribution and descriptive statistics."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    if "ai_autonomy_dependency_category" not in df.columns:
        return {
            "status": "error",
            "message": "Column 'ai_autonomy_dependency_category' not found in dataset.",
        }

    category_counts = df["ai_autonomy_dependency_category"].fillna("unknown").astype(str).value_counts(dropna=False)
    category_percentages = (category_counts / len(df)).round(4)

    response: dict[str, Any] = {
        "status": "ok",
        "total_rows": int(len(df)),
        "npi_category_counts": _to_json_ready(category_counts.to_dict()),
        "npi_category_percentages": _to_json_ready(category_percentages.to_dict()),
    }

    if "ai_autonomy_dependency_index" in df.columns:
        response["npi_score_stats"] = {
            "mean": _to_json_ready(df["ai_autonomy_dependency_index"].mean()),
            "std": _to_json_ready(df["ai_autonomy_dependency_index"].std()),
            "min": _to_json_ready(df["ai_autonomy_dependency_index"].min()),
            "max": _to_json_ready(df["ai_autonomy_dependency_index"].max()),
            "q25": _to_json_ready(df["ai_autonomy_dependency_index"].quantile(0.25)),
            "q50": _to_json_ready(df["ai_autonomy_dependency_index"].quantile(0.50)),
            "q75": _to_json_ready(df["ai_autonomy_dependency_index"].quantile(0.75)),
        }

    return response


def get_executive_summary(lang: str = "en") -> dict[str, Any]:
    """Generate (and cache) an executive summary based on NLP distributions."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    normalized_lang = _normalize_language(lang)

    cached = _EXECUTIVE_CACHE.get(normalized_lang)
    if cached:
        return {"status": "ok", "executive_summary": cached}

    required_columns = [
        "sentiment_label",
        "topic_id",
        "ai_autonomy_dependency_category",
    ]
    missing = [col for col in required_columns if col not in df.columns]
    if missing:
        return {
            "status": "error",
            "message": f"Missing columns for executive summary: {', '.join(missing)}.",
        }

    sentiment_distribution = _to_json_ready(
        df["sentiment_label"]
        .fillna("unknown")
        .astype(str)
        .value_counts(dropna=False)
        .to_dict()
    )
    topic_distribution = _to_json_ready(
        df["topic_id"]
        .fillna("unknown")
        .astype(str)
        .value_counts(dropna=False)
        .head(5)
        .to_dict()
    )
    npi_distribution = _to_json_ready(
        df["ai_autonomy_dependency_category"]
        .fillna("unknown")
        .astype(str)
        .value_counts(dropna=False)
        .to_dict()
    )

    language_instruction = (
        "Generate the executive summary in Spanish."
        if normalized_lang == "es"
        else "Generate the executive summary in English."
    )

    prompt = textwrap.dedent(
        f"""
        {language_instruction}

        You are an AI organizational behavior analyst.

        Sentiment distribution: {sentiment_distribution}
        Top topics: {topic_distribution}
        AI autonomy/dependency risk distribution: {npi_distribution}

        Provide:
        1. Key sentiment insights
        2. Dominant discussion themes
        3. Behavioral risk implications
        4. Recommended leadership actions

        Structure clearly.
        """
    ).strip()

    summary_text = call_llm(prompt)
    if summary_text is not None:
        summary_text = summary_text.strip()

    if not summary_text:
        summary_text = _build_fallback_summary(
            normalized_lang,
            sentiment_distribution,
            topic_distribution,
            npi_distribution,
        )

    _EXECUTIVE_CACHE[normalized_lang] = summary_text

    return {
        "status": "ok",
        "executive_summary": summary_text,
    }


def get_strategic_summary() -> dict[str, Any]:
    """Return high-level strategic analytics combining NLP + ML signals."""
    df = _load_dataframe()
    if df is None:
        return _dataset_error_payload()

    engineered_df = _load_engineered_dataframe()
    if engineered_df is None:
        return _engineered_dataset_error_payload()

    total_rows = len(df)
    if total_rows == 0:
        return {
            "status": "ok",
            "kpis": {},
            "ml_nlp_correlation": {},
            "radar_metrics": {},
            "top_topics_table": [],
        }

    high_risk_percent = _percent_of_category(df, "ai_autonomy_dependency_category", "high")
    neutral_sentiment_percent = _percent_of_category(df, "sentiment_label", "neutral")
    npi_series = _safe_numeric_series(df, "ai_autonomy_dependency_index")
    avg_npi_score = float(round(npi_series.mean(), 2)) if not npi_series.empty else 0.0
    top_risk_topic = _determine_top_risk_topic(df) or ""

    kpis = {
        "high_ai_autonomy_dependency_risk_percent": high_risk_percent,
        "neutral_sentiment_percent": neutral_sentiment_percent,
        "avg_npi_score": avg_npi_score,
        "top_risk_topic": top_risk_topic,
    }

    engineered_total = len(engineered_df)
    ml_overlap = 0.0
    if (
        engineered_total > 0
        and "dropout_risk" in engineered_df.columns
        and "ai_autonomy_dependency_category" in engineered_df.columns
    ):
        dropout_series = pd.to_numeric(engineered_df["dropout_risk"], errors="coerce").fillna(0)
        npi_series_engineered = (
            engineered_df["ai_autonomy_dependency_category"]
            .fillna("")
            .astype(str)
            .str.lower()
        )
        overlap = ((dropout_series == 1) & (npi_series_engineered == "high")).sum()
        ml_overlap = round(float(overlap) / engineered_total * 100, 2)

    ml_nlp_correlation = {
        "dropout_high_and_npi_high_percent": ml_overlap,
    }

    sentiment_positive = 0.0
    if "sentiment_label" in df.columns and not df.empty:
        sentiment_positive = (
            df["sentiment_label"].fillna("").astype(str).str.lower() == "positive"
        ).sum()
        sentiment_positive = round(float(sentiment_positive) / len(df), 4)

    autonomy_mean = _normalized_mean(_safe_numeric_series(df, "autonomy_signal_score"))
    dependency_mean = _normalized_mean(_safe_numeric_series(df, "topic_risk_score"))
    motivation_mean = _normalized_mean(_safe_numeric_series(df, "delta_motivation_score"))

    radar_metrics = {
        "sentiment_positivity": sentiment_positive,
        "autonomy_signal": autonomy_mean,
        "dependency_signal": dependency_mean,
        "motivation_proxy": motivation_mean,
        "risk_level": round(high_risk_percent / 100, 4),
    }

    top_topics_table = _build_top_topics_table(df)

    return {
        "status": "ok",
        "kpis": _to_json_ready(kpis),
        "ml_nlp_correlation": _to_json_ready(ml_nlp_correlation),
        "radar_metrics": _to_json_ready(radar_metrics),
        "top_topics_table": _to_json_ready(top_topics_table),
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
        "ai_autonomy_dependency_index": _to_json_ready(row.get("ai_autonomy_dependency_index")),
        "ai_autonomy_dependency_category": _to_json_ready(row.get("ai_autonomy_dependency_category")),
        "full_text": _to_json_ready(row.get("full_text")),
    }

    return {
        "status": "ok",
        "employee": payload,
    }
