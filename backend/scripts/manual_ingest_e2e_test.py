"""
Manual end-to-end ingestion test for the canonical survey dataset.
- Uses the real backend ingestion path (FastAPI test client)
- Uploads backend/data/raw/survey_raw.xlsx
- Prints ingestion summary and verifies DB state
"""
import os

import pandas as pd
from app.main import app
from fastapi.testclient import TestClient
from supabase import create_client

# Setup test client
client = TestClient(app)

# Path to canonical dataset
DATASET_PATH = "backend/data/raw/survey_raw.xlsx"

# Upload the file using the real ingestion endpoint
with open(DATASET_PATH, "rb") as f:
    response = client.post(
        "/api/v1/upload/surveys",
        files={"file": ("survey_raw.xlsx", f, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
    )

print("Ingestion response:")
print(response.status_code)
print(response.json())

# DB verification
SUPABASE_URL = os.environ["SUPABASE_URL"]

if os.environ.get("SUPABASE_SERVICE_KEY"):
    print("DEBUG: Usando SUPABASE_SERVICE_KEY para la conexión a Supabase.")
    SUPABASE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
elif os.environ.get("SUPABASE_KEY"):
    print("DEBUG: Usando SUPABASE_KEY (anon/public) para la conexión a Supabase.")
    SUPABASE_KEY = os.environ["SUPABASE_KEY"]
else:
    raise RuntimeError("No se encontró ninguna clave SUPABASE_SERVICE_KEY ni SUPABASE_KEY en el entorno.")
supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

# Count total survey_responses
data = supabase.table("survey_responses").select("id_empleado,survey_completed_at,dedupe_key").execute()
df = pd.DataFrame(data.data)
print(f"Total survey_responses in DB: {len(df)}")

# Check for duplicate (id_empleado, survey_completed_at)
duplicates = df.duplicated(subset=["id_empleado", "survey_completed_at"]).sum()
print(f"Duplicate (id_empleado, survey_completed_at) rows: {duplicates}")

# Check for duplicate dedupe_key
dedupe_dupes = df["dedupe_key"].duplicated().sum()
print(f"Duplicate dedupe_key values: {dedupe_dupes}")
