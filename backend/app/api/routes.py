from __future__ import annotations

from fastapi import APIRouter, File, HTTPException, UploadFile

from backend.app.models.schemas import (
    ChatRequest,
    ChatResponse,
    DashboardSummaryResponse,
    NLPRequest,
    NLPResponse,
    SurveyUploadResponse,
)
from backend.app.services.analytics import build_dashboard_summary
from backend.app.services.chat_orchestrator import create_chat_response_orchestrated
from backend.app.services.data_store import repository
from backend.app.services.nlp import analyze_comments

api_router = APIRouter(prefix="/api/v1", tags=["evaluai"])


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
