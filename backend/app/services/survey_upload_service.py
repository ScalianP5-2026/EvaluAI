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


class SurveyUploadService:
    """Service for handling CSV survey uploads."""
    
    def __init__(self, supabase: Client):
        """
        Initialize with Supabase client.
        
        Args:
            supabase: Initialized Supabase client
        """
        self.supabase = supabase
    
    def process_csv_upload(self, file_content: bytes, filename: str) -> SurveyUploadResponse:
        """
        Process a CSV file upload end-to-end.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename (for logging)
            
        Returns:
            SurveyUploadResponse with detailed results
            
        Raises:
            ValueError: If file is invalid or not CSV
        """
        logger.info(f"Processing CSV upload: {filename}")
        
        # Validate file type
        if not filename.lower().endswith(".csv"):
            raise ValueError("File must be a CSV file")
        
        # Decode CSV
        try:
            csv_text = file_content.decode("utf-8-sig")
        except UnicodeDecodeError:
            logger.error("Failed to decode file as UTF-8")
            raise ValueError("File must be UTF-8 encoded")
        
        # Parse CSV
        valid_rows = []
        invalid_rows = []
        errors = []
        
        try:
            reader = csv.DictReader(StringIO(csv_text), delimiter=";")
            
            if reader.fieldnames is None:
                raise ValueError("CSV file is empty or malformed")
            
            # Normalize column names (lowercase, strip)
            normalized_headers = [h.strip().lower() if h else h for h in reader.fieldnames]
            logger.info(f"CSV columns detected: {len(reader.fieldnames)} columns")
            
            # Process each row
            for row_num, row in enumerate(reader, start=2):  # Start at 2 (row 1 is header)
                try:
                    # Normalize row dict keys: lowercase and strip
                    normalized_row = {
                        k.strip().lower() if k else k: v 
                        for k, v in row.items() if k and v
                    }
                    
                    # Validate with Pydantic
                    validated = EmployeeSurveyRow(**normalized_row)
                    
                    # Check that employee_id exists
                    if not validated.id_empleado:
                        errors.append(SurveyUploadError(
                            row=row_num,
                            error="Missing required field: id_empleado"
                        ))
                        invalid_rows.append(row_num)
                        continue
                    
                    valid_rows.append((row_num, validated))
                    
                except ValidationError as e:
                    # Collect first error message for this row
                    error_msg = "; ".join([f"{err['loc'][0]}: {err['msg']}" for err in e.errors()][:1])
                    errors.append(SurveyUploadError(
                        row=row_num,
                        error=error_msg
                    ))
                    invalid_rows.append(row_num)
                    
                except Exception as e:
                    errors.append(SurveyUploadError(
                        row=row_num,
                        error=f"Unexpected error: {str(e)}"
                    ))
                    invalid_rows.append(row_num)
        
        except Exception as e:
            logger.error(f"CSV parsing error: {e}")
            raise ValueError(f"Failed to parse CSV: {str(e)}")
        
        # Total rows (excluding header)
        total_rows = len(valid_rows) + len(invalid_rows)
        
        logger.info(
            f"CSV validation complete: {len(valid_rows)} valid, {len(invalid_rows)} invalid"
        )
        
        if not valid_rows:
            logger.warning("No valid rows to insert")
            return SurveyUploadResponse(
                total_rows=total_rows,
                valid_rows=len(valid_rows),
                invalid_rows=len(invalid_rows),
                inserted_rows=0,
                skipped_duplicates=0,
                errors=[e.dict() for e in errors[:10]]
            )
        
        # Check for duplicates and try to insert
        inserted_count, skipped_count = self._insert_rows(valid_rows)
        
        logger.info(
            f"Upload complete: {inserted_count} inserted, {skipped_count} duplicates skipped"
        )
        
        return SurveyUploadResponse(
            total_rows=total_rows,
            valid_rows=len(valid_rows),
            invalid_rows=len(invalid_rows),
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
