"""
Survey Upload Endpoint - POST /api/v1/upload/surveys

Handles CSV file uploads for employee survey data.
Validates, deduplicates, and inserts into Supabase employees table.
"""

import logging

from app.config import get_supabase_client
from app.models.survey_upload_schema import SurveyUploadResponse
from app.services.survey_upload_service import SurveyUploadService
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["surveys"])


def get_upload_service(supabase: Client = Depends(get_supabase_client)) -> SurveyUploadService:
    """Dependency: Initialize survey upload service."""
    return SurveyUploadService(supabase)


@router.post(
    "/upload/surveys",
    response_model=SurveyUploadResponse,
    summary="Upload employee survey CSV",
    description="Upload a CSV file containing employee survey data. Returns insert summary with error details."
)
async def upload_surveys(
    file: UploadFile = File(..., description="CSV file with employee survey data (semicolon-delimited)"),
    service: SurveyUploadService = Depends(get_upload_service)
) -> SurveyUploadResponse:
    """
    Upload and process a CSV survey file.
    
    Expected CSV format:
    - Encoding: UTF-8
    - Delimiter: Semicolon (;)
    - Required column: id_empleado
    - Header row: Column names
    
    Returns:
    - total_rows: Total rows in CSV (excluding header)
    - valid_rows: Rows that passed validation
    - invalid_rows: Rows that failed validation  
    - inserted_rows: Rows successfully inserted to Supabase
    - skipped_duplicates: Rows skipped due to duplicate employee_id
    - errors: List of validation errors (first 10)
    
    Status Codes:
    - 200: Upload processed (some/all rows may have failed)
    - 400: Invalid file type or encoding
    - 422: No valid rows to insert
    """
    
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="File must have a filename")
    
    if not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a CSV file (.csv)")
    
    # Read file
    MAX_SIZE = 5 * 1024 * 1024
    try:
        content = await file.read()
    except Exception as e:
        logger.error(f"Error reading file: {e}")
        raise HTTPException(status_code=400, detail="Failed to read file")

    if not content:
        raise HTTPException(status_code=400, detail="File is empty")

    # Validate file size (max 5MB) after reading to avoid relying on file.size
    if len(content) > MAX_SIZE:
        actual_mb = len(content) / (1024 * 1024)
        raise HTTPException(
            status_code=400,
            detail=f"File too large ({actual_mb:.1f}MB, max 5MB)"
        )
    
    # Process CSV
    try:
        result = service.process_csv_upload(content, file.filename)
        
        # Log upload summary
        logger.info(
            f"Survey upload summary: {result.inserted_rows} inserted, "
            f"{result.skipped_duplicates} duplicates, "
            f"{result.invalid_rows} invalid"
        )
        
        # If no rows were inserted or skipped as duplicates, return 422
        if result.inserted_rows == 0 and result.skipped_duplicates == 0 and result.valid_rows > 0:
            raise HTTPException(
                status_code=422,
                detail="No rows could be inserted. Check error details."
            )
        
        return result
        
    except ValueError as e:
        logger.error(f"Validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
        
    except Exception as e:
        logger.error(f"Unexpected error processing CSV: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your upload. Please try again."
        )
