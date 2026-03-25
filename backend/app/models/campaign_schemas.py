from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CampaignBase(BaseModel):
    title: str
    description: Optional[str] = None
    wave: Optional[str] = None
    source: Optional[str] = None
    form_provider: Optional[str] = None
    form_url: Optional[str] = None

class CampaignCreate(CampaignBase):
    is_active: Optional[bool] = None

class CampaignUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    wave: Optional[str] = None
    source: Optional[str] = None
    form_provider: Optional[str] = None
    form_url: Optional[str] = None
    is_active: Optional[bool] = None

class CampaignResponse(CampaignBase):
    id: str
    is_active: bool
    created_by: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)

class CampaignListResponse(BaseModel):
    campaigns: list[CampaignResponse]
