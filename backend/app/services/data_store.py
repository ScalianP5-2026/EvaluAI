from __future__ import annotations

import logging
from io import StringIO
from pathlib import Path

import pandas as pd
from app.config import settings

logger = logging.getLogger(__name__)

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

OPEN_TEXT_MAX_LENGTH = 500


class DataRepository:
    def __init__(self, surveys_path: str, courses_path: str, mentors_path: str) -> None:
        self.base_dir = Path(__file__).resolve().parents[2]
        self.surveys_path = self._resolve_path(surveys_path)
        self.courses_path = self._resolve_path(courses_path)
        self.mentors_path = self._resolve_path(mentors_path)

        logger.info(f"DataRepository base_dir: {self.base_dir}")
        logger.info(f"Surveys path resolved: {self.surveys_path} (exists={self.surveys_path.exists()})")

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
            logger.warning(f"CSV file not found: {path}")
            return pd.DataFrame()
        df = pd.read_csv(path, encoding="utf-8-sig")
        df.columns = [str(col).replace("\ufeff", "").strip() for col in df.columns]
        return df

    def _load_surveys(self, path: Path) -> pd.DataFrame:
        if not path.exists():
            logger.error(f"Survey file not found: {path}")
            return pd.DataFrame(columns=REQUIRED_SURVEY_COLUMNS)
        suffix = path.suffix.lower()
        if suffix in {".xls", ".xlsx"}:
            engine = "openpyxl" if suffix == ".xlsx" else "xlrd"
            dataframe = pd.read_excel(path, engine=engine)
        else:
            dataframe = pd.read_csv(path)
        logger.info(f"Loaded {len(dataframe)} survey rows from {path}")
        return self._normalize_surveys(dataframe)

    def _normalize_surveys(self, dataframe: pd.DataFrame) -> pd.DataFrame:
        normalized = dataframe.copy()
        normalized.columns = [
            str(column).replace("\ufeff", "").strip() for column in normalized.columns
        ]

        aliases = {
            "empleado_id": "employee_id",
            "id_empleado": "employee_id",
            "departamento": "role",
            "indice_motivacion": "motivation",
            "frecuencia_uso_ia": "ai_usage",
            "indice_autoeficacia": "self_efficacy",
            "indice_desarrollo_talento": "talent_development",
            "antiguedad_empresa": "experience_years",
            "indice_aceptacion_ia": "acceptance",
            "comentarios_experiencia_ia": "open_experience_ai_learning",
            "sugerencias_mejora": "open_training_needs",
            "comment": "open_experience_ai_learning",
            "last_goal": "open_training_needs",
            "open_experience": "open_experience_ai_learning",
            "experience_ai": "open_experience_ai_learning",
            "ai_learning_comment": "open_experience_ai_learning",
            "open_challenge": "open_challenges_ai_usage",
            "ai_challenges_comment": "open_challenges_ai_usage",
            "training_comment": "open_training_needs",
            "sector": "role",
        }

        for source, target in aliases.items():
            if source in normalized.columns and target not in normalized.columns:
                normalized[target] = normalized[source]

        derived_numeric = {
            "motivation": [
                "M1_estimulante",
                "M2_aumenta_interes",
                "M3_aporta_valor",
                "M4_mayor_esfuerzo",
            ],
            "self_efficacy": [
                "AE1_resolver_problemas",
                "AE2_confianza_digital",
                "AE3_uso_eficaz",
                "AE4_seguridad_aplicacion",
            ],
            "talent_development": [
                "D1_mejora_competencias",
                "D2_preparado_retos",
                "D3_amplia_habilidades",
                "D4_aprendizaje_autonomo",
            ],
            "acceptance": [
                "AT1_rendimiento",
                "AT2_facilita_aprendizaje",
                "AT3_facilidad_uso",
                "AT4_integracion_positiva",
            ],
        }
        for target, source_columns in derived_numeric.items():
            if target in normalized.columns:
                continue
            available = [col for col in source_columns if col in normalized.columns]
            if not available:
                continue
            numeric_block = normalized[available].apply(pd.to_numeric, errors="coerce")
            normalized[target] = numeric_block.mean(axis=1)

        for column in REQUIRED_SURVEY_COLUMNS:
            if column in normalized.columns:
                continue
            normalized[column] = "" if column in {"ai_usage", "last_goal", "comment", "role"} else 0

        official_open_text_columns = [
            "open_experience_ai_learning",
            "open_challenges_ai_usage",
            "open_training_needs",
        ]
        for column in official_open_text_columns:
            if column not in normalized.columns:
                normalized[column] = ""
            normalized[column] = (
                normalized[column]
                .fillna("")
                .astype(str)
                .str.slice(0, OPEN_TEXT_MAX_LENGTH)
            )

        if (
            "comment" not in normalized.columns
            or normalized["comment"].fillna("").astype(str).str.strip().eq("").all()
        ):
            normalized["comment"] = normalized["open_experience_ai_learning"]
        if (
            "last_goal" not in normalized.columns
            or normalized["last_goal"].fillna("").astype(str).str.strip().eq("").all()
        ):
            normalized["last_goal"] = normalized["open_training_needs"]

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
        ordered_columns = REQUIRED_SURVEY_COLUMNS + [
            column for column in normalized.columns if column not in REQUIRED_SURVEY_COLUMNS
        ]
        return normalized[ordered_columns]

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
