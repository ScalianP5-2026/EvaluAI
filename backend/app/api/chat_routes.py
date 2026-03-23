"""
Chat Routes: Endpoints del chatbot.
POST /api/v1/chat/query - Enviar mensaje
GET /api/v1/chat/history - Obtener historial
"""

import logging
import json
import uuid
from datetime import datetime
from typing import Optional

from app.api.access_control import is_rrhh_department
from app.api.auth_routes import get_current_user
from app.chatbot.conversation import ConversationMemory
from app.chatbot.data_manager import DataManager
from app.chatbot.domain_tracking import TrainingSessionTracker
from app.chatbot.foundry_client import FoundryChatClient
from app.chatbot.gemini_client import GeminiChatClient
from app.chatbot.hybrid_rag import HybridRAGOrchestrator
from app.chatbot.prompt_builder import PromptBuilder
from app.chatbot.rag_metrics import record_hybrid_rag_event
from app.chatbot.response_parser import parse_response
from app.models.auth_schemas import EmployeeInfo
from app.models.chat_schemas import (
    ChatRequest,
    ChatResponse,
    ChatTurn,
    ConversationHistoryRequest,
    ErrorResponse,
    InsightsData,
    RecommendationData,
)
from app.services.kpi_engine import (
    calculate_acceptance_distribution,
    calculate_ai_usage_vs_autoeficacia_correlation,
    calculate_department_segmentation,
    calculate_dependency_risk_distribution,
    calculate_motivation_by_ai_usage,
)
from app.services.ml_client import get_ml_client
from fastapi import APIRouter, Depends, HTTPException, status
from supabase import Client

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["chat"])

# Dependency: obtener cliente Supabase (inicializado en main.py lifespan)
def get_supabase_client() -> Client:
    """
    Obtains Supabase client singleton initialized during app lifespan.
    
    The client is initialized once in main.py during app startup and
    reused across all requests via dependency injection.
    
    Returns:
        Client: Supabase async client instance
    
    Raises:
        RuntimeError: If Supabase client not initialized
    """
    from app.config import get_supabase_client as _get_db
    return _get_db()

def get_data_manager(supabase: Client = Depends(get_supabase_client)) -> DataManager:
    """Dependency: Datamanager inicializado."""
    return DataManager(supabase)




def _load_recent_history_for_user(
    supabase: Client,
    user_id: str,
    limit: int = 8,
) -> list[dict[str, str]]:
    """
    Load recent turns from the latest session for this user.

    Returns turns in chronological order.
    """
    try:
        sessions = (
            supabase.table("chat_sessions")
            .select("id")
            .eq("employee_id", user_id)
            .order("started_at", desc=True)
            .limit(1)
            .execute()
        )
        if not sessions.data:
            return []

        session_id = sessions.data[0].get("id")
        if not session_id:
            return []

        turns_response = (
            supabase.table("chat_turns")
            .select("role, message, created_at")
            .eq("session_id", session_id)
            .order("created_at", desc=False)
            .limit(limit)
            .execute()
        )

        turns: list[dict[str, str]] = []
        for turn in turns_response.data or []:
            role = turn.get("role", "")
            content = turn.get("message", "")
            if role in ("user", "assistant") and content:
                if role == "assistant":
                    content = _extract_assistant_message(content)
                turns.append({"role": role, "content": content})
        return turns
    except Exception as exc:
        logger.warning("Could not preload chat history for %s: %s", user_id, exc)
        return []


def _extract_assistant_message(content: str) -> str:
    """
    Normalize assistant content for UI/history.

    Older rows may contain full JSON blobs from LLM output. For those, extract
    only the human-readable `message` field.
    """
    if not isinstance(content, str):
        return str(content)

    text = content.strip()
    if not text:
        return ""

    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:].strip()

    if not text.startswith("{"):
        return content

    try:
        payload = json.loads(text)
        message = payload.get("message")
        if isinstance(message, str) and message.strip():
            return message
    except Exception:
        pass

    return content

# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# POST /api/v1/chat/query
# ---------------------------------------------------------------------------

@router.post("/chat/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    dm: DataManager = Depends(get_data_manager),
    supabase: Client = Depends(get_supabase_client),
    current_user: EmployeeInfo = Depends(get_current_user),
) -> ChatResponse:
    """
    Endpoint principal del chatbot.
        Flujo:
    1. Load employee context (si no viene en request)
    2. Create session
    3. Build prompt (initial)
    4. Query Gemini
    5. Parse response
    6. Save to Supabase
    7. Return ChatResponse
    
    Args:
        request: ChatRequest con user_id, message
        dm: DataManager (inyectado)
        client: GeminiChatClient (inyectado)
        supabase: Supabase client (inyectado)
    
    Returns:
        ChatResponse con mensaje + insights + recomendaciones
    """
    try:
        if (
            current_user.employee_id != request.user_id
            and not is_rrhh_department(current_user.department)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own chatbot session",
            )

        session_id = str(uuid.uuid4())
        logger.info(f"New chat session: {session_id} for user {request.user_id} using provider {request.provider}")
        
        from app.config import GEMINI_API_KEY
        if request.provider.lower() in ("foundry", "azure", "azure_openai", "azure_foundry"):
            client = FoundryChatClient()
        else:
            client = GeminiChatClient(api_key=GEMINI_API_KEY)
        
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 1. LOAD EMPLOYEE CONTEXT
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        # Always load canonical employee context from DB so the LLM can access
        # complete profile data for factual questions.
        base_employee_ctx = dm.get_employee_context(request.user_id)
        if not base_employee_ctx:
            logger.warning(f"Employee {request.user_id} not found in DB")
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Employee {request.user_id} not found"
            )

        # Optional request context can override non-critical fields, but we
        # preserve canonical full-profile payload from Supabase.
        if request.employee_context:
            employee_ctx = {**base_employee_ctx, **request.employee_context}
            employee_ctx["employee_full_profile"] = base_employee_ctx.get(
                "employee_full_profile", {}
            )
            logger.info("Merged provided context on top of DB employee context")
        else:
            employee_ctx = base_employee_ctx

        retrieved_facts = dm.get_retrieved_facts_for_query(
            user_message=request.message,
            employee_ctx=employee_ctx,
        )
        employee_ctx["retrieved_facts"] = retrieved_facts
        # Do not pass full raw profile to the LLM; keep structured retrieved facts only.
        employee_ctx.pop("employee_full_profile", None)
        logger.info(
            "Structured retrieval scope for %s: %s",
            request.user_id,
            retrieved_facts.get("scope", []),
        )
             
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 2. LOAD HYBRID RAG CONTEXT (STRUCTURED + FILE)
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        similar_prof_data = dm.get_similar_profiles(
            department=employee_ctx.get("department", "Unknown"),
            ai_usage_frequency=employee_ctx.get("ai_usage_frequency", 3),
            education_level=employee_ctx.get("education_level", "Unknown"),
        )
        dept_insights_raw = dm.get_department_insights(
            department=employee_ctx.get("department", "Unknown")
        )
        dept_insights_text = (
            "; ".join(f"{k}: {v}" for k, v in dept_insights_raw.items())
            if dept_insights_raw
            else "N/A"
        )

        rag_ctx = {
            "similar_profiles_summary": similar_prof_data.get("summary", "N/A"),
            "department_insights": dept_insights_text,
            "avg_improvement": similar_prof_data.get("avg_improvement", 24),
            "risk_flags": [],
            "top_courses": [],
            "recommended_mentors": [],
            "relevant_programs": [],
        }

        hybrid = HybridRAGOrchestrator(dm)
        hybrid_context = hybrid.run(
            user_message=request.message,
            employee_ctx=base_employee_ctx,
            top_k_courses=5,
            top_k_mentors=3,
        )

        ranked_courses = hybrid_context.get("ranked_courses", []) or []
        ranked_mentors = hybrid_context.get("ranked_mentors", []) or []
        recommended_programs = (
            hybrid_context.get("recommended_programs", []) or ranked_courses[:3]
        )

        rag_ctx["top_courses"] = [
            {
                "title": item.get("title"),
                "avg_autoeficacia_improvement": (item.get("metadata") or {}).get(
                    "avg_autoeficacia_improvement"
                ),
                "avg_completion_rate": (item.get("metadata") or {}).get(
                    "avg_completion_rate"
                ),
                "department": (item.get("metadata") or {}).get("department"),
                "skill_level": (item.get("metadata") or {}).get("skill_level"),
                "source": item.get("source"),
                "score": item.get("score"),
                "reasons": item.get("reasons", []),
            }
            for item in ranked_courses
        ]

        rag_ctx["recommended_mentors"] = [
            {
                "nombre": item.get("title"),
                "mentor_initials": (item.get("metadata") or {}).get("mentor_initials")
                or (item.get("metadata") or {}).get("nombre_codigo"),
                "especialidades": (item.get("metadata") or {}).get("especialidades")
                or (item.get("metadata") or {}).get("expertise"),
                "role": (item.get("metadata") or {}).get("role"),
                "competencia_level": (item.get("metadata") or {}).get(
                    "competencia_level"
                ),
                "disponibilidad": (item.get("metadata") or {}).get("disponibilidad")
                or (item.get("metadata") or {}).get("availability"),
                "email": (item.get("metadata") or {}).get("email"),
                "teams": (item.get("metadata") or {}).get("teams"),
                "contact_channel": (item.get("metadata") or {}).get(
                    "contact_channel"
                ),
                "source": item.get("source"),
                "score": item.get("score"),
                "reasons": item.get("reasons", []),
            }
            for item in ranked_mentors
        ]

        rag_ctx["relevant_programs"] = [
            {
                "title": item.get("title"),
                "department": (item.get("metadata") or {}).get("department"),
                "skill_level": (item.get("metadata") or {}).get("skill_level"),
                "avg_autoeficacia_improvement": (item.get("metadata") or {}).get(
                    "avg_autoeficacia_improvement"
                ),
                "avg_completion_rate": (item.get("metadata") or {}).get(
                    "avg_completion_rate"
                ),
                "source": item.get("source"),
                "score": item.get("score"),
                "reasons": item.get("reasons", []),
            }
            for item in recommended_programs
        ]

        rag_ctx["hybrid_context"] = {
            "query_understanding": hybrid_context.get("query_understanding", {}),
            "tool_trace": hybrid_context.get("tool_trace", []),
            "evaluation": hybrid_context.get("evaluation", {}),
            "citations": hybrid_context.get("citations", []),
        }

        record_hybrid_rag_event(
            {
                "session_id": session_id,
                "employee_id": request.user_id,
                "query": request.message,
                "query_understanding": hybrid_context.get("query_understanding", {}),
                "evaluation": hybrid_context.get("evaluation", {}),
                "tool_trace": hybrid_context.get("tool_trace", []),
                "top_course_titles": [
                    item.get("title") for item in rag_ctx.get("top_courses", [])[:5]
                ],
                "top_mentor_names": [
                    item.get("nombre")
                    for item in rag_ctx.get("recommended_mentors", [])[:3]
                ],
            }
        )

        logger.info(
            "Hybrid RAG loaded: courses=%s, mentors=%s, programs=%s",
            len(rag_ctx.get("top_courses", [])),
            len(rag_ctx.get("recommended_mentors", [])),
            len(rag_ctx.get("relevant_programs", [])),
        )

        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 2.5 GET ML SCORES
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        ml_client = get_ml_client()
        employee_profile = {
            "motivation": employee_ctx.get("motivation", 5.0),
            "autoeficacia": employee_ctx.get("self_efficacy", 5.0),
            "ai_usage": employee_ctx.get("ai_usage_frequency", 3),
            "edad": employee_ctx.get("age", 30),
            "antiguedad": employee_ctx.get("years_in_company", 5)
        }
        ml_scores = ml_client.get_employee_scores(employee_profile)
        rag_ctx["ml_scores"] = ml_scores
        
        logger.info(f"ML scores obtained: recommendation={ml_scores.get('recommendation_score')}, "
                   f"risk={ml_scores.get('risk_score')}, confidence={ml_scores.get('confidence')}")
        
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 2.6 HYBRID RAG CONTEXT READY
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # Mentors and programs are already included in Hybrid RAG output.

        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 3. INITIALIZE SESSION OBJECTS
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        memory = ConversationMemory(request.user_id)
        tracker = TrainingSessionTracker(session_id, request.user_id)
        pb = PromptBuilder()

        previous_turns = _load_recent_history_for_user(supabase, request.user_id)
        for turn in previous_turns:
            memory.add_turn(turn["role"], turn["content"])
                
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 4. BUILD PROMPT (INITIAL)
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        # Always include current user message in prompt construction.
        prompt = pb.build_contextual_prompt(
            user_message=request.message,
            user_context=employee_ctx,
            rag_context=rag_ctx,
            history=memory.get_history(),
            ml_scores=rag_ctx.get("ml_scores"),
        )
        
        logger.info("Prompt built, querying LLM provider...")
        
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 5. QUERY GEMINI
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        response_text = await client.query(prompt, memory.get_history())
        
        logger.info("LLM response received")
        
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 6. PARSE RESPONSE
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
                
        parsed = parse_response(response_text)
        
        if not parsed.get("success"):
            logger.error(f"Failed to parse response: {parsed.get('raw')}")
            # Fallback: retornar mensaje raw
            chat_response = ChatResponse(
                message=response_text,
                session_id=session_id,
                insights=InsightsData(
                    general="Procesando tu solicitud...",
                    department="",
                    personal="",
                ),
                recommendations=None,
                risk_alert=None
            )
            return chat_response
        
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 7. UPDATE MEMORY
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        assistant_message = parsed.get("message", response_text)
        memory.add_turn("user", request.message)
        memory.add_turn("assistant", assistant_message)
        
        # Extract metadata from conversation
        metadata = memory.extract_metadata()
        
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 8. BUILD CHAT RESPONSE
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
                
        recommendations = None
        if parsed.get("recommendations"): 
            recommendations = RecommendationData(
                course=parsed["recommendations"].get("course"),
                rationale=parsed["recommendations"].get("rationale"),
                plan_30_days=parsed["recommendations"].get("plan_30_days")
            )
        
        insights = parsed.get("insights", {})
        chat_response = ChatResponse(
            message=assistant_message,
            session_id=session_id,
            recommendations=recommendations,
            insights=InsightsData(
                general=insights.get("general", ""),
                department=insights.get("department", ""),
                personal=insights.get("personal", "")
            ),
            risk_alert=parsed.get("risk_alert")
        )
        
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        # 9. SAVE TO SUPABASE
        # â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”â”
        
        try:
            # Save chat_sessions
            supabase.table("chat_sessions").insert({
                "id": session_id,
                "employee_id": request.user_id,
                "started_at": datetime.utcnow().isoformat(),
                "goal_detected": metadata.get("goal_detected", False),
                "primary_goal": metadata.get("primary_goal"),
                "goal_clarity": metadata.get("goal_clarity"),
                "conversation_depth": metadata.get("conversation_depth", 1),
                "recommendation_generated": recommendations is not None
            }).execute()
            
            # Save chat_turns (user turn)
            supabase.table("chat_turns").insert({
                "session_id": session_id,
                "role": "user", 
                "message": request.message,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Save chat_turns (assistant turn)
            supabase.table("chat_turns").insert({
                "session_id": session_id,
                "role": "assistant",
                "message": assistant_message,
                "created_at": datetime.utcnow().isoformat()
            }).execute()
            
            # Save recommendation if exists
            if recommendations:
                supabase.table("recommendation_events").insert({
                    "employee_id": request.user_id,
                    "session_id": session_id,
                    "course_recommended": recommendations.course,
                    "plan_generated": bool(recommendations.plan_30_days),
                    "created_at": datetime.utcnow().isoformat()
                }).execute()
            
            logger.info(f"Session data saved to Supabase: {session_id}")
        
        except Exception as e:
            logger.error(f"Error saving to Supabase: {e}")
            # No fallar, continuar de todas formas
        
        logger.info(f"Chat query completed successfully: {session_id}")
        return chat_response
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error in chat_query: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing chat request"
        )
        
            
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•
# GET /api/v1/chat/history
# â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•â•

@router.get("/chat/history", response_model=list[ChatTurn])
async def get_chat_history(
    user_id: str,
    limit: int = 10,
    supabase: Client = Depends(get_supabase_client),
    current_user: EmployeeInfo = Depends(get_current_user),
) -> list[ChatTurn]:
    """
    Obtiene el historial de conversaciÃ³n de un empleado.
    
    Args:
        user_id: ID del empleado
        limit: NÃºmero mÃ¡ximo de turnos (default 10)
        supabase: Supabase client
    
    Returns:
        List[ChatTurn] ordenado por timestamp descendente
    """
    
    try:
        if (
            current_user.employee_id != user_id
            and not is_rrhh_department(current_user.department)
        ):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only access your own chatbot history",
            )
        # Fetch Ãºltimo session
        sessions = supabase.table("chat_sessions").select("id").eq(
            "employee_id", user_id
        ).order("started_at", desc=True).limit(1).execute()
        
        if not sessions.data:
            logger.info(f"No chat history for user {user_id}")
            return []
        
        session_id = sessions.data[0]["id"]
        
        # Fetch turnos
        turns_response = supabase.table("chat_turns").select(
            "role, message, created_at"
        ).eq("session_id", session_id).order(
            "created_at", desc=True
        ).limit(limit).execute()

        # Keep API contract: return newest `limit` turns, but in chronological
        # order for proper chat rendering.
        ordered_turns = list(reversed(turns_response.data or []))

        turns = [
            ChatTurn(
                role=turn["role"],
                content=(
                    _extract_assistant_message(turn["message"])
                    if turn["role"] == "assistant"
                    else turn["message"]
                ),
                timestamp=turn["created_at"]
            )
            for turn in ordered_turns
        ]
        
        logger.info(f"Retrieved {len(turns)} turns for user {user_id}")
        return turns
    
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chat history"
        )            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            

