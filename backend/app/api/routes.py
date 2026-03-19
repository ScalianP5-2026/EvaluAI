"""
⚠️ DEPRECATED MODULE: This router is no longer used in the application.

REASON FOR DEPRECATION:
- This module's endpoints have been superseded by separate, focused routers:
  * chat_routes.py → /api/v1/chat/* endpoints (ACTIVE)
  * kpi_routes.py → /api/v1/kpi/* endpoints (ACTIVE)
  
- The endpoints defined here are listed below but NOT registered in main.py:
  * GET /api/v1/dashboard/summary [UNUSED]
  * POST /api/v1/surveys/upload [UNUSED]
  * POST /api/v1/chat/query [DUPLICATE - chat_routes.py is used instead]
  * POST /api/v1/nlp/analyze [UNUSED]

- The frontend does NOT call any of these endpoints.

MIGRATION PATH:
If any of these endpoints are needed in the future:
1. Review the implementation below
2. Migrate logic to the appropriate router (chat_routes.py, kpi_routes.py, or create new)
3. Remove duplicate POST /chat/query
4. Test thoroughly before re-registration in main.py
5. Remove this file once migration is complete

To revive this router:
1. Uncomment the import in app/api/__init__.py
2. Register in main.py: app.include_router(api_router)
3. Test all endpoints before deploying

This file is kept for reference and historical context.
Last verified: 2026-03-10 (Post-merge stabilization branch)
"""

from __future__ import annotations

from app.config import settings
from app.models.schemas import (
    ChatRequest,
    ChatResponse,
    DashboardSummaryResponse,
    NLPRequest,
    NLPResponse,
    SurveyUploadResponse,
)
from app.services.analytics import build_dashboard_summary
from app.services.chat_orchestrator import create_chat_response_orchestrated
from app.services.data_store import repository
from app.services.nlp import analyze_comments
from fastapi import APIRouter, File, HTTPException, UploadFile

api_router = APIRouter(prefix=settings.api_prefix, tags=["evaluai"])


@api_router.get("/dashboard/summary", response_model=DashboardSummaryResponse)
def get_dashboard_summary() -> DashboardSummaryResponse:
    surveys_df = repository.get_surveys()
    payload = build_dashboard_summary(surveys_df)
    return DashboardSummaryResponse(**payload)


@api_router.post("/surveys/upload", response_model=SurveyUploadResponse)
async def upload_surveys(file: UploadFile = File(...)) -> SurveyUploadResponse:
    filename = file.filename or ""
    if not filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")

    rows_loaded = repository.update_surveys_from_csv(content)
    return SurveyUploadResponse(
        rows_loaded=rows_loaded,
        message=f"Survey dataset updated with {rows_loaded} rows",
    )


@api_router.post("/chat/query", response_model=ChatResponse)
def query_chatbot(request: ChatRequest) -> ChatResponse:
    payload = create_chat_response_orchestrated(request, repository)
    return ChatResponse(**payload)


@api_router.post("/nlp/analyze", response_model=NLPResponse)
def analyze_feedback(request: NLPRequest) -> NLPResponse:
    comments = request.comments or []
    if request.text_blob:
        comments.extend(
            line.strip()
            for line in request.text_blob.splitlines()
            if line.strip()
        )

    if not comments:
        raise HTTPException(status_code=400, detail="Provide comments or text_blob")

    payload = analyze_comments(comments)
    return NLPResponse(**payload)
