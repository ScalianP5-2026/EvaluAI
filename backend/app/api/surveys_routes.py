"""
Survey Upload Endpoint - POST /api/v1/upload/surveys

Handles CSV file uploads for employee survey data.
Validates, deduplicates, and inserts into Supabase employees table.
"""

import logging

from app.config import get_supabase_client
from app.models.survey_upload_schema import SurveyUploadResponse
from app.services.survey_upload_service import SurveyFileFormatError, SurveyUploadService, SurveyValidationError
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
    service: SurveyUploadService = Depends(get_upload_service)
) -> SurveyUploadResponse:
    """
    Upload and process a CSV survey file. Requires campaign_id.
    - campaign_id: Must be provided and valid. All rows will be associated with this campaign.
    - If a row is missing wave, it will inherit the wave from the campaign.
    - All rows will have source set to 'bulk_upload'.
    - Deduplication, date normalization, and batch tracking are preserved.
    """
    # Validate file type
    if not file.filename:
        raise HTTPException(status_code=400, detail="No file uploaded.")

    # Validate campaign_id
    if not campaign_id:
        raise HTTPException(status_code=422, detail="campaign_id is required.")

    try:
        return service.process_csv_upload(await file.read(), file.filename, campaign_id=campaign_id)
    except SurveyFileFormatError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except SurveyValidationError as e:
        raise HTTPException(status_code=422, detail=str(e))
