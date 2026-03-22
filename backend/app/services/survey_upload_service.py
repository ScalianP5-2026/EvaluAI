"""
Survey Upload Service - CSV processing and validation logic.

Handles:
- CSV parsing and normalization
- Row-by-row validation
- Duplicate detection
- Batch insertion into Supabase
"""

import csv
import logging
from io import BytesIO, StringIO
from typing import BinaryIO

from app.models.survey_upload_schema import (
    EmployeeSurveyRow,
    SurveyUploadError,
    SurveyUploadResponse,
)
from pydantic import ValidationError
from supabase import Client

logger = logging.getLogger(__name__)


IMPORT_TYPE = "survey_responses"  # Matches allowed value in DB

class SurveyUploadService:
    """Service for handling CSV survey uploads."""
    
    def __init__(self, supabase: Client):
        """
        Initialize with Supabase client.
        
        Args:
            supabase: Initialized Supabase client
        """
        self.supabase = supabase
    
    def process_csv_upload(self, file_content: bytes, filename: str, campaign_id: str = None) -> SurveyUploadResponse:
        """
        Process a survey file upload (.csv, .xls, .xlsx) end-to-end.
        """
        import uuid

        import pandas as pd
        from app.services.data_store import DataRepository
        logger.info(f"Processing survey upload: {filename}")

        # Detect file type
        ext = filename.lower().split('.')[-1]
        if ext not in {"csv", "xls", "xlsx"}:
            raise ValueError("File must be .csv, .xls, or .xlsx")

        # Parse file to DataFrame
        try:
            if ext == "csv":
                df = pd.read_csv(StringIO(file_content.decode("utf-8-sig")), sep=';')
            else:
                # Excel: read from bytes
                df = pd.read_excel(BytesIO(file_content), engine="openpyxl" if ext == "xlsx" else "xlrd")
        except Exception as e:
            logger.error(f"Failed to parse file: {e}")
            raise ValueError(f"Failed to parse file: {e}")


        # --- Campaign association required ---
        if campaign_id is None:
            raise ValueError("campaign_id is required for manual survey upload.")

        # Load campaign to inherit wave if needed
        campaign = None
        try:
            campaign_result = self.supabase.table("survey_campaigns").select("id,wave").eq("id", campaign_id).single().execute()
            campaign = campaign_result.data
        except Exception as e:
            logger.error(f"Failed to load campaign {campaign_id}: {e}")
            raise ValueError(f"Invalid campaign_id: {campaign_id}")
        if not campaign:
            raise ValueError(f"Invalid campaign_id: {campaign_id}")
        campaign_wave = campaign.get("wave")

        # Normalize and validate
        class NoLoadDataRepository(DataRepository):
            def __init__(self):
                pass
        repo = NoLoadDataRepository()
        norm_df = repo._normalize_surveys(df)
        def compute_dedupe_key(row):
            emp = str(row.get("id_empleado", "")).strip().upper()
            ts = str(row.get("survey_completed_at", "")).strip()
            return f"{emp}_{ts}" if emp and ts else ""
        norm_df["dedupe_key"] = norm_df.apply(compute_dedupe_key, axis=1)

        # --- Begin normalization for campaign association ---
        norm_df["campaign_id"] = campaign_id
        norm_df["source"] = "bulk_upload"
        # Inherit wave from campaign if missing/blank
        if "wave" in norm_df.columns:
            norm_df["wave"] = norm_df["wave"].apply(lambda x: campaign_wave if pd.isna(x) or str(x).strip() == "" else str(x).strip())
        else:
            norm_df["wave"] = campaign_wave
        # Normalize import_batch_id: set to None if blank
        if "import_batch_id" in norm_df.columns:
            norm_df["import_batch_id"] = norm_df["import_batch_id"].apply(lambda x: None if pd.isna(x) or str(x).strip() == "" else x)
        # --- End normalization for campaign association ---

        # Prepare import_batches fields
        import_type = IMPORT_TYPE
        status = "pending"

        # Validation and deduplication
        errors = []
        valid_rows = []
        invalid_rows = []
        seen = set()
        for idx, row in norm_df.iterrows():
            key = (row.get("id_empleado"), row.get("survey_completed_at"))
            # Required fields and valid timestamp
            ts = row.get("survey_completed_at")
            if (
                not row.get("id_empleado")
                or not ts
                or ts == "__INVALID__"
            ):
                errors.append(SurveyUploadError(row=idx+2, error="Missing or invalid id_empleado or survey_completed_at (must be ISO8601, not blank, not unparseable)"))
                invalid_rows.append(idx)
                continue
            # Deduplication in batch
            if key in seen:
                errors.append(SurveyUploadError(row=idx+2, error="Duplicate in upload: (id_empleado, survey_completed_at)"))
                invalid_rows.append(idx)
                continue
            seen.add(key)
            valid_rows.append((idx, row))

        # Check for existing duplicates in DB (Supabase)
        inserted_count = 0
        skipped_count = 0
        first_fail_printed = False
        # Only allow columns that exist in survey_responses table
        persisted_columns = [
            "id_empleado",
            "edad",
            "genero",
            "departamento",
            "antiguedad_empresa",
            "nivel_educativo",
            "rol_tecnico",
            "sector",
            "frecuencia_uso_ia",
            "usa_chatgpt",
            "usa_gemini",
            "usa_copilot",
            "usa_lms_ia",
            "usa_otra_ia",
            "herramienta_principal",
            "prefiere_humano_vs_ia",
            "nivel_integracion_ia",
            "at1_rendimiento",
            "at2_facilita_aprendizaje",
            "at3_facilidad_uso",
            "at4_integracion_positiva",
            "ae1_resolver_problemas",
            "ae2_confianza_digital",
            "ae3_uso_eficaz",
            "ae4_seguridad_aplicacion",
            "m1_estimulante",
            "m2_aumenta_interes",
            "m3_aporta_valor",
            "m4_mayor_esfuerzo",
            "e1_adaptacion",
            "e2_feedback_util",
            "e3_aplicable_trabajo",
            "e4_aprendizaje_ritmo",
            "d1_mejora_competencias",
            "d2_preparado_retos",
            "d3_amplia_habilidades",
            "d4_aprendizaje_autonomo",
            "c1_confio_sin_verificar",
            "c2_dificil_sin_ia",
            "c3_pensamiento_critico",
            "c4_reflexiono_calidad",
            "open_positive_experience",
            "open_difficulties_and_training_needs",
            "survey_completed_at",
            "wave",
            "source",
            "import_batch_id",
            "dedupe_key",
            "campaign_id"
        ]
        for idx, row in valid_rows:
            try:
                # Check for existing duplicate
                query = self.supabase.table("survey_responses").select("id_empleado,survey_completed_at").eq("id_empleado", row["id_empleado"]).eq("survey_completed_at", row["survey_completed_at"]).execute()
                if query.data and len(query.data) > 0:
                    skipped_count += 1
                    errors.append(SurveyUploadError(row=idx+2, error="Duplicate in database: (id_empleado, survey_completed_at)"))
                    continue
                # Insert row with only persisted columns, handle UUID metadata fields
                insert_data = {}
                for k in persisted_columns:
                    if k not in row:
                        continue
                    v = row[k]
                    # Normalize all optional fields: never send empty string, always None if blank
                    if k in ("import_batch_id", "campaign_id", "wave", "source"):
                        if v is None or (isinstance(v, str) and v.strip() == ""):
                            insert_data[k] = None
                        else:
                            insert_data[k] = v
                    else:
                        if v is not None:
                            insert_data[k] = v
                if not first_fail_printed:
                    first_fail_printed = True
                self.supabase.table("survey_responses").insert(insert_data).execute()
                inserted_count += 1
            except Exception as e:
                errors.append(SurveyUploadError(row=idx+2, error=f"Insert error: {str(e)}"))
                invalid_rows.append(idx)

        # Create import_batches record and get batch id
        import datetime
        batch_id = None
        batch_status = status
        total_rows = len(norm_df)
        valid_count = inserted_count
        invalid_count = len(invalid_rows)
        # Only count errors (duplicates and invalids) once
        rejected_count = len(errors)
        try:
            # Create batch as pending
            response = self.supabase.table("import_batches").insert({
                "import_type": import_type,
                "status": status,
                "source_filename": filename,
                "rows_received": total_rows,
                "rows_inserted": inserted_count,
            }).execute()
            if response.data and len(response.data) > 0:
                batch_id = response.data[0]["id"]
        except Exception as e:
            logger.warning(f"Failed to create import_batches record: {e}")
        if not batch_id:
            logger.warning("No batch_id returned from import_batches insert; error tracking may fail.")

        # Store errors in import_batch_errors (aligned to schema), only if batch_id is valid
        if batch_id:
            for err in errors:
                try:
                    error_payload = {
                        "batch_id": batch_id,
                        "row_number": err.row,
                        "error_message": err.error,
                    }
                    self.supabase.table("import_batch_errors").insert(error_payload).execute()
                except Exception as e:
                    logger.warning(f"Failed to store import_batch_errors: {e}")

        # Finalize batch status and update import_batches
        try:
            # Status logic
            if inserted_count > 0:
                if skipped_count > 0 or len(errors) > 0:
                    batch_status = "completed_with_errors"
                else:
                    batch_status = "completed"
            else:
                # No rows inserted, but process completed (all duplicates/errors)
                batch_status = "completed_with_errors"
            # Set finished_at and updated_at at the true end
            finished_at = datetime.datetime.utcnow().isoformat()
            updated_at = finished_at
            if batch_id:
                self.supabase.table("import_batches").update({
                    "status": batch_status,
                    "rows_received": total_rows,
                    "rows_inserted": inserted_count,
                    "rows_rejected": rejected_count,
                    "finished_at": finished_at,
                    "updated_at": updated_at
                }).eq("id", batch_id).execute()
        except Exception as e:
            logger.warning(f"Failed to finalize import_batches record: {e}")

        return SurveyUploadResponse(
            total_rows=total_rows,
            valid_rows=valid_count,
            invalid_rows=invalid_count,
            inserted_rows=inserted_count,
            skipped_duplicates=skipped_count,
            errors=[e.dict() for e in errors[:10]]
        )
    
    def _insert_rows(self, valid_rows: list[tuple[int, EmployeeSurveyRow]]) -> tuple[int, int]:
        """
        Insert validated rows into Supabase, handling duplicates.
        
        Args:
            valid_rows: List of (row_num, validated_row) tuples
            
        Returns:
            Tuple of (inserted_count, skipped_count)
        """
        inserted_count = 0
        skipped_count = 0
        
        # Try bulk insert first (more efficient)
        if len(valid_rows) > 0:
            rows_to_insert = [row.to_supabase_employee() for _, row in valid_rows]
            
            try:
                response = self.supabase.table("employees").insert(rows_to_insert).execute()
                if response.data:
                    inserted_count = len(response.data)
                    logger.info(f"Bulk insert successful: {inserted_count} rows")
                    return inserted_count, 0
            except Exception as e:
                error_str = str(e).lower()
                if "409" in error_str or "duplicate" in error_str or "conflict" in error_str:
                    logger.info("Bulk insert failed due to duplicates, attempting row-by-row insert")
                else:
                    logger.error(f"Bulk insert error: {e}")
                    # Rethrow if not a duplicate issue
                    if "409" not in str(e):
                        raise
        
        # Fall back to row-by-row insert to handle partial duplicates
        for row_num, validated_row in valid_rows:
            try:
                employee_data = validated_row.to_supabase_employee()
                response = self.supabase.table("employees").insert([employee_data]).execute()
                
                if response.data:
                    inserted_count += 1
                    
            except Exception as e:
                error_str = str(e).lower()
                if "409" in error_str or "duplicate" in error_str or "conflict" in error_str:
                    skipped_count += 1
                    logger.debug(f"Row {row_num}: Duplicate employee_id, skipped")
                else:
                    logger.error(f"Row {row_num} insert error: {e}")
        
        return inserted_count, skipped_count
