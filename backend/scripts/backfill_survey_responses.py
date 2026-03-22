"""
Backfill/enrich the first 100 survey_responses rows from canonical dataset.
Fills: open_positive_experience, open_difficulties_and_training_needs, survey_completed_at, dedupe_key, updated_at
"""
import os
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    load_dotenv = None
from datetime import datetime
from datetime import datetime as dt

import pandas as pd
from supabase import Client, create_client

# Load .env if needed
if not os.environ.get("SUPABASE_URL") or not os.environ.get("SUPABASE_KEY"):
    env_path = Path(__file__).parent.parent.parent / ".env"
    if load_dotenv and env_path.exists():
        load_dotenv(dotenv_path=env_path)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
# Prefer SUPABASE_SERVICE_KEY for admin scripts, fallback to SUPABASE_KEY
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_KEY") or os.environ.get("SUPABASE_KEY")
if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL and SUPABASE_KEY (or SUPABASE_SERVICE_KEY) must be set as environment variables or in a .env file at the project root.")
# Debug: print partial values for verification
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def compute_dedupe_key(id_empleado, survey_completed_at):
    emp = str(id_empleado).strip().upper()
    ts = str(survey_completed_at).strip()
    return f"{emp}_{ts}" if emp and ts else ""

def backfill_from_file(file_path, limit=None):
    ext = str(file_path).lower().split('.')[-1]
    if ext == 'csv':
        df = pd.read_csv(file_path)
    elif ext in ('xls', 'xlsx'):
        df = pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file extension: {ext}. Use .csv, .xls, or .xlsx")
    if limit is not None:
        df = df.head(limit)
    # Fail loudly if duplicate id_empleado in input
    if df["id_empleado"].duplicated().any():
        dups = df[df["id_empleado"].duplicated(keep=False)]["id_empleado"].tolist()
        raise ValueError(f"Duplicate id_empleado values in input: {dups}")
    for _, row in df.iterrows():
        id_empleado = row.get("id_empleado")
        survey_completed_at = row.get("survey_completed_at")
        # Convertir fecha al formato ISO si es string tipo DD/MM/YYYY HH:MM:SS
        survey_completed_at_iso = None
        if isinstance(survey_completed_at, str):
            try:
                # Soporta tanto DD/MM/YYYY HH:MM:SS como DD/MM/YYYY
                if "/" in survey_completed_at:
                    if len(survey_completed_at.strip().split(" ")) == 2:
                        survey_completed_at_iso = dt.strptime(survey_completed_at, "%d/%m/%Y %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
                    else:
                        survey_completed_at_iso = dt.strptime(survey_completed_at, "%d/%m/%Y").strftime("%Y-%m-%d")
                else:
                    survey_completed_at_iso = survey_completed_at
            except Exception:
                survey_completed_at_iso = survey_completed_at
        elif pd.notna(survey_completed_at):
            # Si es datetime o timestamp
            try:
                survey_completed_at_iso = pd.to_datetime(survey_completed_at).strftime("%Y-%m-%d %H:%M:%S")
            except Exception:
                survey_completed_at_iso = str(survey_completed_at)
        dedupe_key = compute_dedupe_key(id_empleado, survey_completed_at_iso or survey_completed_at)
        # Find existing legacy row by id_empleado only (for legacy backfill)
        query = supabase.table("survey_responses").select("id").eq("id_empleado", id_empleado).execute()
        if query.data and len(query.data) > 0:
            record_id = query.data[0]["id"]
            update_fields = {}
            for col in ["open_positive_experience", "open_difficulties_and_training_needs"]:
                if col in row and pd.notna(row[col]):
                    update_fields[col] = row[col]
            # Solo guardar survey_completed_at si hay valor válido
            if survey_completed_at_iso:
                update_fields["survey_completed_at"] = survey_completed_at_iso
            update_fields["dedupe_key"] = dedupe_key
            update_fields["updated_at"] = datetime.utcnow().isoformat()
            supabase.table("survey_responses").update(update_fields).eq("id", record_id).execute()

if __name__ == "__main__":
    import argparse
    import sys
    parser = argparse.ArgumentParser(description="Backfill survey_responses from Excel/CSV file.")
    parser.add_argument("file", help="Path to dataset file (.csv, .xls, .xlsx)")
    parser.add_argument("--limit", type=int, default=None, help="Limit to first N rows (excluding header)")
    args = parser.parse_args()
    backfill_from_file(args.file, limit=args.limit)