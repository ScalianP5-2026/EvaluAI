from __future__ import annotations

from io import StringIO
from pathlib import Path

import pandas as pd

from backend.app.config import settings

REQUIRED_SURVEY_COLUMNS = [
    "employee_id",
    "role",
    "motivation",
    "ai_usage",
    "self_efficacy",
    "talent_development",
    "experience_years",
    "acceptance",
    "comment",
    "last_goal",
]


class DataRepository:
    def __init__(self, surveys_path: str, courses_path: str, mentors_path: str) -> None:
        self.base_dir = Path(__file__).resolve().parents[2]
        self.surveys_path = self._resolve_path(surveys_path)
        self.courses_path = self._resolve_path(courses_path)
        self.mentors_path = self._resolve_path(mentors_path)

        self.surveys_df = self._load_surveys(self.surveys_path)
        self.courses_df = self._load_csv(self.courses_path)
        self.mentors_df = self._load_csv(self.mentors_path)

    def _resolve_path(self, raw_path: str) -> Path:
        as_path = Path(raw_path)
        if as_path.is_absolute():
            return as_path
        return self.base_dir / as_path

    def _load_csv(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame()
        return pd.read_csv(path)

    def _load_surveys(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            return pd.DataFrame(columns=REQUIRED_SURVEY_COLUMNS)
        dataframe = pd.read_csv(path)
        return self._normalize_surveys(dataframe)

    def _normalize_surveys(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        normalized = dataframe.copy()
        normalized.columns = [
            str(column).replace("\ufeff", "").strip() for column in normalized.columns
        ]

        aliases = {
            "empleado_id": "employee_id",
            "departamento": "role",
            "indice_motivacion": "motivation",
            "frecuencia_uso_ia": "ai_usage",
            "indice_autoeficacia": "self_efficacy",
            "indice_desarrollo_talento": "talent_development",
            "antiguedad_empresa": "experience_years",
            "indice_aceptacion_ia": "acceptance",
            "comentarios_experiencia_ia": "comment",
            "sugerencias_mejora": "last_goal",
        }

        for source, target in aliases.items():
            if source in normalized.columns and target not in normalized.columns:
                normalized[target] = normalized[source]

        for column in REQUIRED_SURVEY_COLUMNS:
            if column in normalized.columns:
                continue
            normalized[column] = "" if column in {"ai_usage", "last_goal", "comment", "role"} else 0

        normalized["role"] = normalized["role"].fillna("Unknown").astype(str)
        normalized["ai_usage"] = (
            normalized["ai_usage"]
            .apply(_normalize_ai_usage)
            .astype(str)
            .str.lower()
            .str.strip()
        )
        normalized["comment"] = normalized["comment"].fillna("").astype(str)
        normalized["last_goal"] = normalized["last_goal"].fillna("General upskilling").astype(str)

        numeric_cols = [
            "motivation",
            "self_efficacy",
            "talent_development",
            "experience_years",
            "acceptance",
        ]
        for column in numeric_cols:
            normalized[column] = pd.to_numeric(
                normalized[column],
                errors="coerce",
            ).fillna(0.0)

        normalized["employee_id"] = normalized["employee_id"].astype(str)
        return normalized[REQUIRED_SURVEY_COLUMNS]

    def get_surveys(self) -> pd.DataFrame:
        return self.surveys_df.copy()

    def get_courses(self) -> pd.DataFrame:
        return self.courses_df.copy()

    def get_mentors(self) -> pd.DataFrame:
        return self.mentors_df.copy()

    def update_surveys_from_csv(self, raw_content: bytes) -> int:
        parsed = pd.read_csv(StringIO(raw_content.decode("utf-8")))
        self.surveys_df = self._normalize_surveys(parsed)
        return int(len(self.surveys_df))


def _normalize_ai_usage(value: object) -> str:
    numeric_map = {
        1: "never",
        2: "rarely",
        3: "sometimes",
        4: "frequently",
        5: "always",
    }
    text_map = {
        "never": "never",
        "nunca": "never",
        "rarely": "rarely",
        "raramente": "rarely",
        "sometimes": "sometimes",
        "a veces": "sometimes",
        "frequently": "frequently",
        "frecuentemente": "frequently",
        "always": "always",
        "siempre": "always",
    }

    try:
        as_float = float(value)
        rounded = int(round(as_float))
        if rounded in numeric_map:
            return numeric_map[rounded]
    except (TypeError, ValueError):
        pass

    return text_map.get(str(value).strip().lower(), "never")


repository = DataRepository(
    surveys_path=settings.surveys_path,
    courses_path=settings.courses_path,
    mentors_path=settings.mentors_path,
)
