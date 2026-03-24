from app.api.access_control import require_rrhh_access
from app.api.auth_routes import get_current_user
from app.config import get_supabase_client
from app.models.auth_schemas import EmployeeInfo
from app.models.campaign_schemas import (
    CampaignCreate,
    CampaignListResponse,
    CampaignResponse,
    CampaignUpdate,
)
from app.services.campaign_service import CampaignService
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

router = APIRouter(prefix="/api/v1/campaigns", tags=["campaigns"])

def get_campaign_service(supabase: Client = Depends(get_supabase_client)) -> CampaignService:
    return CampaignService(supabase)

@router.get("/", response_model=CampaignListResponse, dependencies=[Depends(require_rrhh_access)])
def list_campaigns(service: CampaignService = Depends(get_campaign_service)):
    """List all survey campaigns (RRHH only)."""
    campaigns = service.list_campaigns()
    return {"campaigns": campaigns}

@router.get("/{campaign_id}", response_model=CampaignResponse, dependencies=[Depends(require_rrhh_access)])
def get_campaign(campaign_id: str, service: CampaignService = Depends(get_campaign_service)):
    """Get a campaign by ID (RRHH only)."""
    campaign = service.get_campaign(campaign_id)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.post("/", response_model=CampaignResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(require_rrhh_access)])
def create_campaign(
    payload: CampaignCreate,
    service: CampaignService = Depends(get_campaign_service),
    current_user: EmployeeInfo = Depends(get_current_user),
):
    """Create a new survey campaign (RRHH only)."""
    campaign = service.create_campaign(payload.dict(exclude_unset=True), created_by=current_user.email)
    return campaign

@router.patch("/{campaign_id}", response_model=CampaignResponse, dependencies=[Depends(require_rrhh_access)])
def update_campaign(
    campaign_id: str,
    payload: CampaignUpdate,
    service: CampaignService = Depends(get_campaign_service),
):
    """Update a survey campaign (RRHH only)."""
    campaign = service.update_campaign(campaign_id, payload.dict(exclude_unset=True))
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.post("/{campaign_id}/activate", response_model=CampaignResponse, dependencies=[Depends(require_rrhh_access)])
def activate_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    """Activate a campaign (RRHH only)."""
    campaign = service.set_active(campaign_id, True)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign

@router.post("/{campaign_id}/deactivate", response_model=CampaignResponse, dependencies=[Depends(require_rrhh_access)])
def deactivate_campaign(
    campaign_id: str,
    service: CampaignService = Depends(get_campaign_service),
):
    """Deactivate a campaign (RRHH only)."""
    campaign = service.set_active(campaign_id, False)
    if not campaign:
        raise HTTPException(status_code=404, detail="Campaign not found")
    return campaign
