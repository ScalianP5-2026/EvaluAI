from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from supabase import Client


class CampaignService:
    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table = "survey_campaigns"

    def list_campaigns(self) -> List[dict]:
        result = self.supabase.table(self.table).select("*").order("created_at", desc=True).execute()
        return result.data or []

    def get_campaign(self, campaign_id: int) -> Optional[dict]:
        result = self.supabase.table(self.table).select("*").eq("id", campaign_id).single().execute()
        return result.data

    def create_campaign(self, payload: dict, created_by: str) -> dict:
        data = payload.copy()
        data["created_by"] = created_by
        data["is_active"] = True
        result = self.supabase.table(self.table).insert(data).execute()
        return result.data[0]

    def update_campaign(self, campaign_id: int, payload: dict) -> Optional[dict]:
        data = payload.copy()
        data["updated_at"] = datetime.utcnow().isoformat()
        result = self.supabase.table(self.table).update(data).eq("id", campaign_id).execute()
        return result.data[0] if result.data else None

    def set_active(self, campaign_id: int, is_active: bool) -> Optional[dict]:
        data = {"is_active": is_active, "updated_at": datetime.utcnow().isoformat()}
        result = self.supabase.table(self.table).update(data).eq("id", campaign_id).execute()
        return result.data[0] if result.data else None
