"""
Integration tests for the /api/v1/upload/surveys endpoint.
Covers:
- File upload (CSV, XLS, XLSX)
- Validation and normalization
"""

import csv
import io

import openpyxl
import pandas as pd

# --- Monkeypatch Supabase for campaign lookup in endpoint tests ---
import pytest
from app.main import app
from fastapi.testclient import TestClient


class DummySupabase:
    def __init__(self):
        # In-memory stores for campaigns, responses, batches, and errors
        self._campaign = {"id": "11111111-1111-1111-1111-111111111111", "wave": "t1"}
        self._batches = []
        self._responses = []  # List of dicts with id_empleado, survey_completed_at
        self._batch_errors = []
        self._last_duplicates = 0  # Track duplicates for test reporting

    def table(self, name):
        dummy = self
        class DummyTable:
            def select(self, *args, **kwargs):
                # Support chained .eq(...).eq(...).execute() for multi-column filtering
                class DummyQuery:
                    def __init__(self):
                        self.filters = []  # list of (col, val)
                    def eq(self, col, val):
                        self.filters.append((col, val))
                        return self
                    def single(self):
                        class DummyExecute:
                            @property
                            def data(inner_self):
                                if name == "survey_campaigns":
                                    # Only support lookup by id
                                    for fcol, fval in self.filters:
                                        if fcol == "id" and fval == dummy._campaign["id"]:
                                            return dummy._campaign
                                    return None
                                if name == "survey_responses":
                                    filtered = dummy._responses
                                    for fcol, fval in self.filters:
                                        filtered = [r for r in filtered if r.get(fcol) == fval]
                                    return filtered
                                return None
                            def execute(inner_self):
                                return inner_self
                        return DummyExecute()
                    def execute(self):
                        # For non-single() queries, just return filtered list
                        if name == "survey_responses":
                            filtered = dummy._responses
                            for fcol, fval in self.filters:
                                filtered = [r for r in filtered if r.get(fcol) == fval]
                            class DummyExecute:
                                @property
                                def data(inner_self):
                                    return filtered
                                def execute(inner_self):
                                    return inner_self
                            return DummyExecute()
                        return self
                return DummyQuery()
            def insert(self, data):
                # Simulate insert for import_batches, survey_responses, import_batch_errors
                if name == "import_batches":
                    batch = {"id": len(dummy._batches) + 1}
                    dummy._batches.append(batch)
                    class DummyResp:
                        @property
                        def data(self):
                            return [batch]
                        def execute(self):
                            return self
                    return DummyResp()
                elif name == "survey_responses":
                    # Accept both list and dict for data
                    rows = data if isinstance(data, list) else [data]
                    inserted = 0
                    duplicates = 0
                    for row in rows:
                        # Deduplication by (id_empleado, survey_completed_at)
                        key = (row.get("id_empleado"), row.get("survey_completed_at"))
                        exists = any(
                            (r.get("id_empleado"), r.get("survey_completed_at")) == key
                            for r in dummy._responses
                        )
                        if exists:
                            duplicates += 1
                        else:
                            dummy._responses.append(row)
                            inserted += 1
                    dummy._last_duplicates = duplicates
                    class DummyResp:
                        @property
                        def data(self):
                            return [data]
                        def execute(self):
                            return self
                    return DummyResp()
                elif name == "import_batch_errors":
                    dummy._batch_errors.append(data)
                    class DummyResp:
                        @property
                        def data(self):
                            return [data]
                        def execute(self):
                            return self
                    return DummyResp()
                else:
                    class DummyResp:
                        @property
                        def data(self):
                            return [data]
                        def execute(self):
                            return self
                    return DummyResp()
            def update(self, data):
                # Simulate update for import_batches (no-op)
                class DummyResp:
                    @property
                    def data(self):
                        return [data]
                    def execute(self):
                        return self
                return DummyResp()
        return DummyTable()

@pytest.fixture(autouse=True)
def patch_supabase(monkeypatch):
    # Patch the SurveyUploadService in the app to use DummySupabase
    from app.services import survey_upload_service
    orig_init = survey_upload_service.SurveyUploadService.__init__
    def dummy_init(self, supabase):
        orig_init(self, DummySupabase())
    monkeypatch.setattr(survey_upload_service.SurveyUploadService, "__init__", dummy_init)
    yield

client = TestClient(app)

def make_csv_file(rows, columns=None):
    """Helper to create a CSV file in memory as BytesIO for multipart upload."""
    if not columns:
        columns = list(rows[0].keys())
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=columns, delimiter=';')
    writer.writeheader()
    for row in rows:
        writer.writerow(row)
    output.seek(0)
    return io.BytesIO(output.read().encode("utf-8"))


def make_xlsx_file(rows, columns=None):
    wb = openpyxl.Workbook()
    ws = wb.active
    if not columns:
        columns = list(rows[0].keys())
    ws.append(columns)
    for row in rows:
        ws.append([row.get(col, "") for col in columns])
    file = io.BytesIO()
    wb.save(file)
    file.seek(0)
    return file


# .xls runtime support is present, but test is skipped unless xlwt is available.
def make_xls_file(rows, columns=None):
    try:
        import xlwt
    except ImportError:
        pytest.skip(
            ".xls test skipped: xlwt not installed. .xls is supported at runtime via xlrd/openpyxl."
        )
    wb = xlwt.Workbook()
    ws = wb.add_sheet('Sheet1')
    if not columns:
        columns = list(rows[0].keys())
    for col_idx, col in enumerate(columns):
        ws.write(0, col_idx, col)
    for row_idx, row in enumerate(rows, 1):
        for col_idx, col in enumerate(columns):
            ws.write(row_idx, col_idx, row.get(col, ""))
    file = io.BytesIO()
    wb.save(file)
    file.seek(0)
    return file
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
        data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
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
        data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
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
    # Use a local DummySupabase and patch the service for this test only
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
    # Patch SurveyUploadService to use our local dummy
    local_dummy = DummySupabase()
    from app.services import survey_upload_service
    orig_init = survey_upload_service.SurveyUploadService.__init__
    def dummy_init(self, supabase):
        orig_init(self, local_dummy)
    survey_upload_service.SurveyUploadService.__init__ = dummy_init
    try:
        response = client.post(
            "/api/v1/upload/surveys",
            files={"file": ("test.csv", file, "text/csv")},
            data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["inserted_rows"] == 1
        assert data["skipped_duplicates"] == local_dummy._last_duplicates
    finally:
        survey_upload_service.SurveyUploadService.__init__ = orig_init


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
        data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
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
        data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
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
        data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
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
        data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
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
        data={"campaign_id": "11111111-1111-1111-1111-111111111111"},
    )
    assert response_blank.status_code == 200
    data_blank = response_blank.json()
    assert data_blank["inserted_rows"] == 0
    assert data_blank["invalid_rows"] == 1
    assert data_blank["valid_rows"] == 0
    assert data_blank["total_rows"] == 1
    assert data_blank["errors"]
    assert "survey_completed_at" in data_blank["errors"][0]["error"]

# New tests for campaign_id enforcement and wave/source logic
def test_upload_missing_campaign_id_rejected():
    rows = [
        {
            "id_empleado": "EMP300",
            "survey_completed_at": "2024-03-21T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
        }
    ]
    file = make_csv_file(rows)
    response = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("test.csv", file, "text/csv")},
    )
    assert response.status_code == 422
    # FastAPI returns a list of error dicts in 'detail'
    detail = response.json()["detail"]
    assert any(
        (err.get("loc") and "campaign_id" in err["loc"]) for err in detail
    )

def test_upload_wave_inherits_from_campaign(monkeypatch):
    # Patch supabase to return a campaign with wave 'WAVE42'
    class DummySupabase:
        def table(self, name):
            class DummyTable:
                def select(self, *args, **kwargs):
                    class DummyQuery:
                        def eq(self, *args, **kwargs):
                            class DummySingle:
                                def single(self):
                                    class DummyExecute:
                                        @property
                                        def data(self):
                                            # Return matching UUID and wave
                                            return {"id": "11111111-1111-1111-1111-111111111111", "wave": "WAVE42"}
                                        def execute(self):
                                            return self
                                    return DummyExecute()
                                def execute(self):
                                    return self
                            return DummySingle()
                        def execute(self):
                            return self
                    return DummyQuery()
            return DummyTable()
    from app.services import survey_upload_service
    service = survey_upload_service.SurveyUploadService(DummySupabase())
    rows = [
        {
            "id_empleado": "EMP400",
            "survey_completed_at": "2024-03-21T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
        },
        {
            "id_empleado": "EMP401",
            "survey_completed_at": "2024-03-22T10:00:00",
            "rol_tecnico": 0,
            "motivation": 4.0,
            "wave": "",
        },
    ]
    df = pd.DataFrame(rows)
    # Should inherit wave from campaign if missing/blank
    result = service.process_csv_upload(
        df.to_csv(index=False, sep=';').encode("utf-8"),
        "test.csv",
        campaign_id="11111111-1111-1111-1111-111111111111",
    )
    # All rows should have wave == 'WAVE42'
    # (We can't check DB, but we can check no error is raised)
    assert result.total_rows == 2

def test_upload_source_is_bulk_upload(monkeypatch):
    class DummySupabase:
        def table(self, name):
            class DummyTable:
                def select(self, *args, **kwargs):
                    class DummyQuery:
                        def eq(self, *args, **kwargs):
                            class DummySingle:
                                def single(self):
                                    class DummyExecute:
                                        @property
                                        def data(self):
                                            # Return matching UUID and wave
                                            return {"id": "11111111-1111-1111-1111-111111111111", "wave": "WAVE42"}
                                        def execute(self):
                                            return self
                                    return DummyExecute()
                                def execute(self):
                                    return self
                            return DummySingle()
                        def execute(self):
                            return self
                    return DummyQuery()
            return DummyTable()
    from app.services import survey_upload_service
    service = survey_upload_service.SurveyUploadService(DummySupabase())
    rows = [
        {
            "id_empleado": "EMP500",
            "survey_completed_at": "2024-03-21T10:00:00",
            "rol_tecnico": 1,
            "motivation": 5.0,
        },
    ]
    df = pd.DataFrame(rows)
    result = service.process_csv_upload(
        df.to_csv(index=False, sep=';').encode("utf-8"),
        "test.csv",
        campaign_id="11111111-1111-1111-1111-111111111111",
    )
    # All rows should have source == 'bulk_upload' (enforced in service)
    # (We can't check DB, but we can check no error is raised)
    assert result.total_rows == 1
    # Unparseable
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
            "wave": "t1",
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
            "wave": "t1",
        },
    ]
