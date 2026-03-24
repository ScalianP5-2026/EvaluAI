"""
Survey Upload Endpoint - POST /api/v1/upload/surveys

Handles CSV file uploads for employee survey data.
Validates, deduplicates, and inserts into Supabase employees table.
"""

import logging

from app.api.access_control import require_rrhh_access
from app.config import get_supabase_client
from app.models.survey_upload_schema import SurveyUploadResponse
from app.services.survey_upload_service import SurveyUploadService
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["surveys"])


def get_upload_service(supabase: Client = Depends(get_supabase_client)) -> SurveyUploadService:
    """Dependency: Initialize survey upload service."""
    return SurveyUploadService(supabase)


@router.post(
    "/upload/surveys",
    response_model=SurveyUploadResponse,
    summary="Upload employee survey CSV (campaign required)",
    description="Upload a CSV file containing employee survey data. Requires campaign_id. Returns insert summary with error details."
)
async def upload_surveys(
    file: UploadFile = File(..., description="CSV file with employee survey data (semicolon-delimited)"),
    campaign_id: str = Form(..., description="ID of the associated survey campaign (required, UUID)"),
    service: SurveyUploadService = Depends(get_upload_service),
    _current_user=Depends(require_rrhh_access),
) -> SurveyUploadResponse:
    """
    Upload and process a CSV survey file. Requires campaign_id.
    - campaign_id: Must be provided and valid. All rows will be associated with this campaign.
    - If a row is missing wave, it will inherit the wave from the campaign.
    - All rows will have source set to 'bulk_upload'.
    - Deduplication, date normalization, and batch tracking are preserved.
    """
    # Validate file presence and extension
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    allowed_exts = (".csv", ".xlsx", ".xls")
    if not file.filename.lower().endswith(allowed_exts):
        raise HTTPException(status_code=400, detail="File must be .csv, .xlsx, or .xls")

    # Validate campaign_id
    if not campaign_id:
        raise HTTPException(status_code=422, detail="campaign_id is required.")

    # Read file once
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
        result = service.process_csv_upload(content, file.filename, campaign_id=campaign_id)

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
        raise HTTPException(status_code=422, detail=str(e))

    except Exception as e:
        logger.error(f"Unexpected error processing CSV: {e}")
        raise HTTPException(
            status_code=500,
            detail="An error occurred processing your upload. Please try again."
        )
