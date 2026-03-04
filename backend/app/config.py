from __future__ import annotations

import os
from dataclasses import dataclass, field


def _csv_env(name: str, default: list[str]) -> list[str]:
    raw = os.getenv(name)
    if not raw:
        return default
    values = [item.strip() for item in raw.split(",")]
    return [item for item in values if item]


def _float_env(name: str, default: float) -> float:
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return float(raw)
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    app_name: str = os.getenv("EVALUAI_APP_NAME", "EvaluAI API")
    app_description: str = os.getenv(
        "EVALUAI_APP_DESCRIPTION",
        "API to evaluate training impact with AI",
    )
    app_version: str = os.getenv("EVALUAI_APP_VERSION", "0.1.0")
    api_prefix: str = os.getenv("EVALUAI_API_PREFIX", "/api/v1")
    allowed_origins: list[str] = field(
        default_factory=lambda: _csv_env("EVALUAI_ALLOWED_ORIGINS", ["*"])
    )

    surveys_path: str = os.getenv(
        "EVALUAI_SURVEYS_PATH",
        "data/datos_encuesta_formacion_ia.csv",
    )
    courses_path: str = os.getenv("EVALUAI_COURSES_PATH", "data/courses.csv")
    mentors_path: str = os.getenv("EVALUAI_MENTORS_PATH", "data/mentors.csv")

    chat_provider: str = os.getenv("EVALUAI_CHAT_PROVIDER", "rule_based")
    azure_foundry_endpoint: str = os.getenv("EVALUAI_AZURE_FOUNDRY_ENDPOINT", "")
    azure_foundry_api_key: str = os.getenv("EVALUAI_AZURE_FOUNDRY_API_KEY", "")
    azure_foundry_model: str = os.getenv("EVALUAI_AZURE_FOUNDRY_MODEL", "")
    azure_foundry_temperature: float = _float_env(
        "EVALUAI_AZURE_FOUNDRY_TEMPERATURE",
        0.2,
    )


settings = Settings()
