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
        # Copy and clean column names
        normalized = dataframe.copy()
        normalized.columns = [str(column).replace("\ufeff", "").strip() for column in normalized.columns]

        # Canonical/legacy mapping: preserve id_empleado as canonical, map to employee_id for compatibility only
        # All other mappings are one-way for compatibility, not destructive
        aliases = {
            # Canonical identifier for survey_responses
            "id_empleado": "id_empleado",  # always present
            # Compatibility for legacy app (employee_id is only for compatibility)
            "empleado_id": "employee_id",
            "departamento": "role",
            "sector": "role",
            "indice_motivacion": "motivation",
            "frecuencia_uso_ia": "ai_usage",
            "indice_autoeficacia": "self_efficacy",
            "indice_desarrollo_talento": "talent_development",
            "antiguedad_empresa": "experience_years",
            "indice_aceptacion_ia": "acceptance",
            # Survey metric columns (map to lowercase)
            "AT1_rendimiento": "at1_rendimiento",
            "AT2_facilita_aprendizaje": "at2_facilita_aprendizaje",
            "AT3_facilidad_uso": "at3_facilidad_uso",
            "AT4_integracion_positiva": "at4_integracion_positiva",
            "AE1_resolver_problemas": "ae1_resolver_problemas",
            "AE2_confianza_digital": "ae2_confianza_digital",
            "AE3_uso_eficaz": "ae3_uso_eficaz",
            "AE4_seguridad_aplicacion": "ae4_seguridad_aplicacion",
            "M1_estimulante": "m1_estimulante",
            "M2_aumenta_interes": "m2_aumenta_interes",
            "M3_aporta_valor": "m3_aporta_valor",
            "M4_mayor_esfuerzo": "m4_mayor_esfuerzo",
            "E1_adaptacion": "e1_adaptacion",
            "E2_feedback_util": "e2_feedback_util",
            "E3_aplicable_trabajo": "e3_aplicable_trabajo",
            "E4_aprendizaje_ritmo": "e4_aprendizaje_ritmo",
            "D1_mejora_competencias": "d1_mejora_competencias",
            "D2_preparado_retos": "d2_preparado_retos",
            "D3_amplia_habilidades": "d3_amplia_habilidades",
            "D4_aprendizaje_autonomo": "d4_aprendizaje_autonomo",
            "C1_confio_sin_verificar": "c1_confio_sin_verificar",
            "C2_dificil_sin_ia": "c2_dificil_sin_ia",
            "C3_pensamiento_critico": "c3_pensamiento_critico",
            "C4_reflexiono_calidad": "c4_reflexiono_calidad",
            # Legacy open-text fields (kept for compatibility only)
            "comentarios_experiencia_ia": "open_experience_ai_learning",
            "sugerencias_mejora": "open_training_needs",
            "open_experience": "open_experience_ai_learning",
            "experience_ai": "open_experience_ai_learning",
            "ai_learning_comment": "open_experience_ai_learning",
            "open_challenge": "open_challenges_ai_usage",
            "ai_challenges_comment": "open_challenges_ai_usage",
            "training_comment": "open_training_needs",
            # Canonical new open-text fields
            "open_positive_experience": "open_positive_experience",
            "open_difficulties_and_training_needs": "open_difficulties_and_training_needs",
            "survey_completed_at": "survey_completed_at",
            "source": "source",
            "import_batch_id": "import_batch_id",
            "wave": "wave",
            "dedupe_key": "dedupe_key",
        }
        # Apply mapping, but never drop id_empleado
        for source, target in aliases.items():
            if source in normalized.columns and target not in normalized.columns:
                normalized[target] = normalized[source]
        # Remove any metric columns that are not canonical (i.e., drop uppercase/raw metric columns)
        metric_cols = [
            "at1_rendimiento", "at2_facilita_aprendizaje", "at3_facilidad_uso", "at4_integracion_positiva",
            "ae1_resolver_problemas", "ae2_confianza_digital", "ae3_uso_eficaz", "ae4_seguridad_aplicacion",
            "m1_estimulante", "m2_aumenta_interes", "m3_aporta_valor", "m4_mayor_esfuerzo",
            "e1_adaptacion", "e2_feedback_util", "e3_aplicable_trabajo", "e4_aprendizaje_ritmo",
            "d1_mejora_competencias", "d2_preparado_retos", "d3_amplia_habilidades", "d4_aprendizaje_autonomo",
            "c1_confio_sin_verificar", "c2_dificil_sin_ia", "c3_pensamiento_critico", "c4_reflexiono_calidad"
        ]
        for col in list(normalized.columns):
            if col.upper() in aliases.keys() and col not in metric_cols and col != col.lower():
                normalized.drop(columns=[col], inplace=True)
        # Apply mapping, but never drop id_empleado
        for source, target in aliases.items():
            if source in normalized.columns and target not in normalized.columns:
                normalized[target] = normalized[source]

        # Ensure id_empleado is always present and string
        if "id_empleado" not in normalized.columns:
            normalized["id_empleado"] = ""
        normalized["id_empleado"] = normalized["id_empleado"].astype(str)

        # Derived numeric fields (Likert averages, preserve decimals)
        derived_numeric = {
            "motivation": ["M1_estimulante", "M2_aumenta_interes", "M3_aporta_valor", "M4_mayor_esfuerzo"],
            "self_efficacy": ["AE1_resolver_problemas", "AE2_confianza_digital", "AE3_uso_eficaz", "AE4_seguridad_aplicacion"],
            "talent_development": ["D1_mejora_competencias", "D2_preparado_retos", "D3_amplia_habilidades", "D4_aprendizaje_autonomo"],
            "acceptance": ["AT1_rendimiento", "AT2_facilita_aprendizaje", "AT3_facilidad_uso", "AT4_integracion_positiva"],
        }
        for target, source_columns in derived_numeric.items():
            if target in normalized.columns:
                continue
            available = [col for col in source_columns if col in normalized.columns]
            if not available:
                continue
            numeric_block = normalized[available].apply(pd.to_numeric, errors="coerce")
            normalized[target] = numeric_block.mean(axis=1)

        # Numeric normalization for Likert/AI usage fields (preserve decimals for averages)
        float_fields = [
            "motivation", "self_efficacy", "talent_development", "acceptance"
        ]
        for col in float_fields:
            if col in normalized.columns:
                normalized[col] = pd.to_numeric(normalized[col], errors="coerce").fillna(0.0)
        if "experience_years" in normalized.columns:
            normalized["experience_years"] = pd.to_numeric(normalized["experience_years"], errors="coerce").fillna(0).astype(int)

        # Explicit boolean normalization for canonical fields
        bool_fields = [
            "rol_tecnico", "usa_chatgpt", "usa_gemini", "usa_copilot", "usa_lms_ia", "usa_otra_ia"
        ]
        for col in bool_fields:
            if col in normalized.columns:
                normalized[col] = normalized[col].apply(lambda x: str(x).strip().lower() in ["1", "true", "yes", "y", "t"]).astype(bool)

        # Ensure all required columns exist
        for column in REQUIRED_SURVEY_COLUMNS:
            if column in normalized.columns:
                continue
            normalized[column] = "" if column in {"ai_usage", "last_goal", "comment", "role"} else 0

        # Canonical open-text fields: always present, never depend on legacy
        for col in ["open_positive_experience", "open_difficulties_and_training_needs"]:
            if col not in normalized.columns:
                normalized[col] = ""
            normalized[col] = (
                normalized[col]
                .fillna("")
                .astype(str)
                .str.slice(0, OPEN_TEXT_MAX_LENGTH)
            )

        # Legacy open-text fields: keep for compatibility, do not depend on them
        for col in ["open_experience_ai_learning", "open_challenges_ai_usage", "open_training_needs"]:
            if col not in normalized.columns:
                normalized[col] = ""
            normalized[col] = (
                normalized[col]
                .fillna("")
                .astype(str)
                .str.slice(0, OPEN_TEXT_MAX_LENGTH)
            )

        # survey_completed_at: accept multiple formats, normalize to canonical ISO8601, mark as '__INVALID__' if unparseable
        def parse_survey_completed_at(val):
            if not isinstance(val, str) or not val.strip():
                return "__INVALID__"
            val = val.strip()
            # Try ISO8601 and pandas default parsing
            try:
                dt = pd.to_datetime(val, errors="raise")
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
            # Try DD/MM/YYYY HH:MM:SS
            try:
                dt = pd.to_datetime(val, format="%d/%m/%Y %H:%M:%S", errors="raise")
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
            # Try DD/MM/YYYY
            try:
                dt = pd.to_datetime(val, format="%d/%m/%Y", errors="raise")
                return dt.strftime("%Y-%m-%dT%H:%M:%S")
            except Exception:
                pass
            return "__INVALID__"

        if "survey_completed_at" in normalized.columns:
            normalized["survey_completed_at"] = [parse_survey_completed_at(v) for v in normalized["survey_completed_at"]]
        else:
            normalized["survey_completed_at"] = "__INVALID__"

        # Traceability fields: preserve if present
        for col in ["source", "import_batch_id", "wave", "dedupe_key"]:
            if col not in normalized.columns:
                normalized[col] = ""
            normalized[col] = normalized[col].fillna("").astype(str)

        # Boolean normalization (example: if any boolean fields are present, normalize to True/False)
        for col in normalized.columns:
            if col.startswith("is_") or col.endswith("_flag"):
                normalized[col] = normalized[col].apply(lambda x: str(x).strip().lower() in ["1", "true", "yes", "y", "t"]).astype(bool)


        # Only experience_years should be cast to int; preserve decimals for Likert averages
        if "experience_years" in normalized.columns:
            normalized["experience_years"] = pd.to_numeric(normalized["experience_years"], errors="coerce").fillna(0).astype(int)

        # AI usage normalization (string mapping)
        if "ai_usage" in normalized.columns:
            normalized["ai_usage"] = (
                normalized["ai_usage"]
                .apply(_normalize_ai_usage)
                .astype(str)
                .str.lower()
                .str.strip()
            )

        # Fill defaults for comment/last_goal
        if "comment" not in normalized.columns or normalized["comment"].fillna("").astype(str).str.strip().eq("").all():
            normalized["comment"] = normalized["open_positive_experience"]
        if "last_goal" not in normalized.columns or normalized["last_goal"].fillna("").astype(str).str.strip().eq("").all():
            normalized["last_goal"] = normalized["open_difficulties_and_training_needs"]

        normalized["role"] = normalized["role"].fillna("Unknown").astype(str)
        normalized["comment"] = normalized["comment"].fillna("").astype(str)
        normalized["last_goal"] = normalized["last_goal"].fillna("General upskilling").astype(str)
        normalized["employee_id"] = normalized["employee_id"].astype(str)

        # Preserve all columns, order with required first
        ordered_columns = REQUIRED_SURVEY_COLUMNS + [
            col for col in normalized.columns if col not in REQUIRED_SURVEY_COLUMNS
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
