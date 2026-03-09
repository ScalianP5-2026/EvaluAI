from __future__ import annotations

from pydantic import BaseModel, Field


class UsageDistributionItem(BaseModel):
    level: str
    count: int


class CorrelationItem(BaseModel):
    metric: str
    value: float


class CategoryCountItem(BaseModel):
    label: str
    count: int


class DashboardSummaryResponse(BaseModel):
    total_employees: int
    avg_motivation: float
    avg_self_efficacy: float
    avg_ai_use_score: float
    avg_age: float
    avg_ai_integration: float
    avg_human_preference: float
    usage_distribution: list[UsageDistributionItem]
    gender_distribution: list[CategoryCountItem]
    department_distribution: list[CategoryCountItem]
    primary_tool_distribution: list[CategoryCountItem]
    ai_tools_usage: list[CategoryCountItem]
    correlations: list[CorrelationItem]
    insights: list[str]


class SurveyUploadResponse(BaseModel):
    rows_loaded: int
    message: str


class ChatRequest(BaseModel):
    employee_role: str
    learning_goal: str
    ai_usage: str = "never"
    self_efficacy: float = Field(default=0.0, ge=0)
    motivation: float = Field(default=0.0, ge=0)


class ChatResponse(BaseModel):
    message: str
    recommended_courses: list[str]
    recommended_mentor: str
    thirty_day_plan: list[str]
    similar_profile_improvement: float


class NLPRequest(BaseModel):
    comments: list[str] | None = None
    text_blob: str | None = None


class TopicItem(BaseModel):
    topic: str
    matches: int


class NLPResponse(BaseModel):
    overall_sentiment: str
    sentiment_score: float
    topics: list[TopicItem]
    group_recommendations: list[str]
