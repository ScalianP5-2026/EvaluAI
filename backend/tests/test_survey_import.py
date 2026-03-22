"""
Integration tests for the /api/v1/upload/surveys endpoint.
Covers:
- File upload (CSV, XLS, XLSX)
- Validation and normalization
- Duplicate rejection
- Traceability fields
- Error reporting
"""

import io

import pandas as pd
from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)



def make_csv_file(rows, columns=None):
    """Helper to create a CSV file in memory as BytesIO for multipart upload."""
    df = pd.DataFrame(rows, columns=columns)
    buf = io.BytesIO()
    df.to_csv(buf, index=False, sep=';', encoding='utf-8')
    buf.seek(0)
    return buf

def make_xlsx_file(rows, columns=None):
    """Helper to create an XLSX file in memory."""
    df = pd.DataFrame(rows, columns=columns)
    buf = io.BytesIO()
    df.to_excel(buf, index=False, engine="openpyxl")
    buf.seek(0)
    return buf


# .xls runtime support is present, but test is skipped unless xlwt is available.
import pytest


def make_xls_file(rows, columns=None):
    pytest.skip(".xls test skipped: xlwt not installed. .xls is supported at runtime via xlrd/openpyxl.")
    # If you want to enable this test, install xlwt and uncomment below:
    # import xlwt
    # df = pd.DataFrame(rows, columns=columns)
    # buf = io.BytesIO()
    # workbook = xlwt.Workbook()
    # sheet = workbook.add_sheet('Sheet1')
    # for col_idx, col in enumerate(df.columns):
    #     sheet.write(0, col_idx, col)
    # for row_idx, row in enumerate(df.values):
    #     for col_idx, value in enumerate(row):
    #         sheet.write(row_idx + 1, col_idx, value)
    # workbook.save(buf)
    # buf.seek(0)
    # return buf
def test_survey_import_xlsx_success():
    """Test successful import of valid survey rows from XLSX."""
    rows = [
        {
            "id_empleado": "EMP010",
            "survey_completed_at": "2024-03-30T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
            "acceptance": 6.0,
        },
        {
            "id_empleado": "EMP011",
            "survey_completed_at": "2024-03-31T10:00:00",
            "rol_tecnico": 0,
            "motivation": 4.0,
            "acceptance": 5.0,
        },
    ]
    file = make_xlsx_file(rows)
    response = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.xlsx", file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_rows"] == 2
    assert data["skipped_duplicates"] == 0
    assert data["invalid_rows"] == 0
    assert data["valid_rows"] == 2
    assert data["total_rows"] == 2
def test_survey_import_xls_success():
    """Test successful import of valid survey rows from XLS."""
    rows = [
        {
            "id_empleado": "EMP020",
            "survey_completed_at": "2024-04-01T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
            "acceptance": 6.0,
        },
        {
            "id_empleado": "EMP021",
            "survey_completed_at": "2024-04-02T10:00:00",
            "rol_tecnico": 0,
            "motivation": 4.0,
            "acceptance": 5.0,
        },
    ]
    file = make_xls_file(rows)
    response = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.xls", file, "application/vnd.ms-excel")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_rows"] == 2
    assert data["skipped_duplicates"] == 0
    assert data["invalid_rows"] == 0
    assert data["valid_rows"] == 2
    assert data["total_rows"] == 2


def test_survey_import_success():
    """Test successful import of valid survey rows."""
    rows = [
        {
            "id_empleado": "EMP001",
            "survey_completed_at": "2024-03-21T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
            "acceptance": 6.0,
            "open_positive_experience": "Muy buena experiencia",
            "open_difficulties_and_training_needs": "Faltó formación",
            "source": "bulk_upload",
            "wave": "1",
        },
        {
            "id_empleado": "EMP002",
            "survey_completed_at": "2024-03-22T10:00:00",
            "rol_tecnico": 0,
            "motivation": 4.0,
            "acceptance": 5.0,
            "open_positive_experience": "Positiva",
            "open_difficulties_and_training_needs": "Ninguna",
            "source": "bulk_upload",
            "wave": "1",
        },
    ]
    file = make_csv_file(rows)
    response = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_rows"] == 2
    assert data["skipped_duplicates"] == 0
    assert data["invalid_rows"] == 0
    assert data["valid_rows"] == 2
    assert data["total_rows"] == 2
    assert isinstance(data["errors"], list)


def test_survey_import_duplicate():
    """Test duplicate survey rejection by (id_empleado, survey_completed_at)."""
    rows = [
        {
            "id_empleado": "EMP003",
            "survey_completed_at": "2024-03-23T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
            "acceptance": 6.0,
        },
        {
            "id_empleado": "EMP003",
            "survey_completed_at": "2024-03-23T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
            "acceptance": 6.0,
        },
    ]
    file = make_csv_file(rows)
    response = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_rows"] == 1
    assert data["skipped_duplicates"] == 1


def test_survey_import_validation_error():
    """Test validation error for missing id_empleado."""
    rows = [
        {
            "survey_completed_at": "2024-03-24T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
        }
    ]
    file = make_csv_file(rows)
    response = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file, "text/csv")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["inserted_rows"] == 0
    assert data["invalid_rows"] == 1
    assert data["valid_rows"] == 0
    assert data["total_rows"] == 1
    assert data["errors"]
    assert "id_empleado" in data["errors"][0]["error"]


def test_survey_import_missing_or_invalid_survey_completed_at():
    """Test validation error for missing or invalid survey_completed_at."""
    # ISO8601
    rows_iso = [
        {
            "id_empleado": "EMP200",
            "survey_completed_at": "2024-03-21T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
        }
    ]
    file_iso = make_csv_file(rows_iso)
    response_iso = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file_iso, "text/csv")},
    )
    assert response_iso.status_code == 200
    data_iso = response_iso.json()
    assert data_iso["inserted_rows"] == 1
    assert data_iso["invalid_rows"] == 0
    assert data_iso["valid_rows"] == 1
    assert data_iso["total_rows"] == 1

    # DD/MM/YYYY HH:MM:SS
    rows_eu = [
        {
            "id_empleado": "EMP201",
            "survey_completed_at": "16/02/2026 19:33:34",
            "rol_tecnico": 1,
            "motivation": 5.0,
        }
    ]
    file_eu = make_csv_file(rows_eu)
    response_eu = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file_eu, "text/csv")},
    )
    assert response_eu.status_code == 200
    data_eu = response_eu.json()
    assert data_eu["inserted_rows"] == 1
    assert data_eu["invalid_rows"] == 0
    assert data_eu["valid_rows"] == 1
    assert data_eu["total_rows"] == 1

    # DD/MM/YYYY
    rows_eu_short = [
        {
            "id_empleado": "EMP202",
            "survey_completed_at": "16/02/2026",
            "rol_tecnico": 1,
            "motivation": 5.0,
        }
    ]
    file_eu_short = make_csv_file(rows_eu_short)
    response_eu_short = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file_eu_short, "text/csv")},
    )
    assert response_eu_short.status_code == 200
    data_eu_short = response_eu_short.json()
    assert data_eu_short["inserted_rows"] == 1
    assert data_eu_short["invalid_rows"] == 0
    assert data_eu_short["valid_rows"] == 1
    assert data_eu_short["total_rows"] == 1

    # Blank
    rows_blank = [
        {
            "id_empleado": "EMP203",
            "survey_completed_at": "",
            "rol_tecnico": 1,
            "motivation": 5.0,
        }
    ]
    file_blank = make_csv_file(rows_blank)
    response_blank = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file_blank, "text/csv")},
    )
    assert response_blank.status_code == 200
    data_blank = response_blank.json()
    assert data_blank["inserted_rows"] == 0
    assert data_blank["invalid_rows"] == 1
    assert data_blank["valid_rows"] == 0
    assert data_blank["total_rows"] == 1
    assert data_blank["errors"]
    assert "survey_completed_at" in data_blank["errors"][0]["error"]

    # Unparseable
    rows_invalid = [
        {
            "id_empleado": "EMP204",
            "survey_completed_at": "not-a-date",
            "rol_tecnico": 1,
            "motivation": 5.0,
        }
    ]
    file_invalid = make_csv_file(rows_invalid)
    response_invalid = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file_invalid, "text/csv")},
    )
    assert response_invalid.status_code == 200
    data_invalid = response_invalid.json()
    assert data_invalid["inserted_rows"] == 0
    assert data_invalid["invalid_rows"] == 1
    assert data_invalid["valid_rows"] == 0
    assert data_invalid["total_rows"] == 1
    assert data_invalid["errors"]
    assert "survey_completed_at" in data_invalid["errors"][0]["error"]
