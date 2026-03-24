from datetime import datetime

import pandas as pd
import pytest
from app.services.data_store import DataRepository


# Subclass to bypass file loading in tests
class TestableDataRepository(DataRepository):
    def __init__(self):
        pass


def test_normalize_surveys_canonical_fields():
    df = pd.DataFrame([
        {
            "id_empleado": "EMP001",
            "rol_tecnico": True,
            "usa_chatgpt": "yes",
            "usa_gemini": 1,
            "usa_copilot": "no",
            "usa_lms_ia": "True",
            "usa_otra_ia": "false",
            "open_positive_experience": "Muy buena experiencia",
            "open_difficulties_and_training_needs": "Faltó formación",
            "survey_completed_at": "2024-03-21T10:00:00",
            "motivation": 3.5,
            "self_efficacy": 4.2,
            "talent_development": 2.8,
            "acceptance": 4.0,
            "source": "importer",
            "import_batch_id": "batch-1",
            "wave": "1",
            "dedupe_key": "EMP001-2024",
        }
    ])
    repo = TestableDataRepository()
    norm = repo._normalize_surveys(df)
    row = norm.iloc[0]
    # Canonical fields
    assert row["id_empleado"] == "EMP001"
    assert row["open_positive_experience"] == "Muy buena experiencia"
    assert row["open_difficulties_and_training_needs"] == "Faltó formación"
    assert row["survey_completed_at"].startswith("2024-03-21")
    # Boolean normalization
    assert row["rol_tecnico"] == True
    assert row["usa_chatgpt"] == True
    assert row["usa_gemini"] == True
    assert row["usa_copilot"] == False
    assert row["usa_lms_ia"] == True
    assert row["usa_otra_ia"] == False
    # Numeric preservation
    assert abs(row["motivation"] - 3.5) < 1e-6
    assert abs(row["self_efficacy"] - 4.2) < 1e-6
    assert abs(row["talent_development"] - 2.8) < 1e-6
    assert abs(row["acceptance"] - 4.0) < 1e-6
    # Traceability
    assert row["source"] == "importer"
    assert row["import_batch_id"] == "batch-1"
    assert row["wave"] == "1"
    assert row["dedupe_key"] == "EMP001-2024"
    # Compatibility
    assert row["employee_id"] == "EMP001"
    # No field loss
    assert "id_empleado" in norm.columns
    assert "employee_id" in norm.columns

def test_normalize_surveys_timestamp_parsing():
    df = pd.DataFrame([
        {"id_empleado": "EMP002", "survey_completed_at": "2024-03-21 10:00:00"},  # ISO8601
        {"id_empleado": "EMP003", "survey_completed_at": "16/02/2026 19:33:34"},  # DD/MM/YYYY HH:MM:SS
        {"id_empleado": "EMP004", "survey_completed_at": "16/02/2026"},  # DD/MM/YYYY
        {"id_empleado": "EMP005", "survey_completed_at": "not-a-date"},  # invalid
        {"id_empleado": "EMP006", "survey_completed_at": ""},  # blank
    ])
    repo = TestableDataRepository()
    norm = repo._normalize_surveys(df)
    # ISO8601
    assert norm.loc[0, "survey_completed_at"] == "2024-03-21T10:00:00"
    # DD/MM/YYYY HH:MM:SS
    assert norm.loc[1, "survey_completed_at"] == "2026-02-16T19:33:34"
    # DD/MM/YYYY
    assert norm.loc[2, "survey_completed_at"] == "2026-02-16T00:00:00"
    # invalid
    assert norm.loc[3, "survey_completed_at"] == "__INVALID__"
    # blank
    assert norm.loc[4, "survey_completed_at"] == "__INVALID__"

def test_normalize_surveys_extra_fields_preserved():
    df = pd.DataFrame([
        {"id_empleado": "EMP004", "extra_field": "should_stay"}
    ])
    repo = TestableDataRepository()
    norm = repo._normalize_surveys(df)
    assert "extra_field" in norm.columns
    assert norm.loc[0, "extra_field"] == "should_stay"
