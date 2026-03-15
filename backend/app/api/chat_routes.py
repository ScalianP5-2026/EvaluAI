"""
Chat Routes: Endpoints del chatbot.
POST /api/v1/chat/query - Enviar mensaje
GET /api/v1/chat/history - Obtener historial
"""

import logging
import uuid
from datetime import datetime
from typing import Optional

from app.chatbot.conversation import ConversationMemory
from app.chatbot.data_manager import DataManager
from app.chatbot.domain_tracking import TrainingSessionTracker
from app.chatbot.gemini_client import GeminiChatClient
from app.chatbot.prompt_builder import PromptBuilder
from app.chatbot.response_parser import parse_response
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

def get_gemini_client() -> GeminiChatClient:
    """Dependency: GeminiChatClient inicializado."""
    from app.config import GEMINI_API_KEY
    return GeminiChatClient(api_key=GEMINI_API_KEY)

# ═══════════════════════════════════════════════════════════════
# POST /api/v1/chat/query
# ═══════════════════════════════════════════════════════════════

@router.post("/chat/query", response_model=ChatResponse)
async def chat_query(
    request: ChatRequest,
    dm: DataManager = Depends(get_data_manager),
    client: GeminiChatClient = Depends(get_gemini_client),
    supabase: Client = Depends(get_supabase_client)
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
        session_id = str(uuid.uuid4())
        logger.info(f"New chat session: {session_id} for user {request.user_id}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 1. LOAD EMPLOYEE CONTEXT
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        if request.employee_context:
            employee_ctx = request.employee_context
            logger.info("Using provided employee context")
        else:
            employee_ctx = dm.get_employee_context(request.user_id)
            if not employee_ctx:
                logger.warning(f"Employee {request.user_id} not found in DB")
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Employee {request.user_id} not found"
                )       
             
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2. LOAD RAG CONTEXT (SQL)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        top_courses = dm.get_top_courses(
            department=employee_ctx.get("department", "Unknown"),
            limit=3
        )
        
        # 1. Obtenemos los datos puros
        similar_prof_data = dm.get_similar_profiles(
            department=employee_ctx.get("department", "Unknown"),
            ai_usage_frequency=employee_ctx.get("ai_usage_frequency", 3),
            education_level=employee_ctx.get("education_level", "Unknown")
        )
        dept_insights_raw = dm.get_department_insights(
            department=employee_ctx.get("department", "Unknown")
        )
        
        # 2. Aplanamos (Flatten) el diccionario de insights a un String legible para la IA
        dept_insights_text = "; ".join(f"{k}: {v}" for k, v in dept_insights_raw.items()) if dept_insights_raw else "N/A"
        
        # 3. Construimos el RAG context EXACTO que espera el PromptBuilder
        rag_ctx = {
            "similar_profiles_summary": similar_prof_data.get("summary", "N/A"),
            "department_insights": dept_insights_text,
            "top_courses": top_courses,
            "avg_improvement": similar_prof_data.get("avg_improvement", 24),
            "risk_flags": [] # Lo inicializamos para que el LLM no falle al buscarlo
        }
        
        logger.info(f"RAG context loaded: {len(rag_ctx.get('top_courses', []))} courses")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2.5 GET ML SCORES
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
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
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2.6 GET MENTOR RECOMMENDATIONS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Extract tecnologías from top courses titles
        tecnologias = [c.get("title", "").split()[0] for c in top_courses]  # Simple: first word
        mentores = dm.get_mentor_recommendations(especialidades=tecnologias, limit=2)
        rag_ctx["recommended_mentors"] = mentores
        
        logger.info(f"Found {len(mentores)} mentor recommendations")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 2.7 GET RELEVANT PROGRAMS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        programas = dm.get_relevant_programs(
            tecnologias=tecnologias,
<<<<<<< HEAD
=======
            nivel=None, # FIX: Evitamos cruzar nivel académico con dificultad de curso
>>>>>>> 520fb0d (fix(chatbot): harmonize RAG context keys and fix strict academic level filtering)
            limit=3
        )
        rag_ctx["relevant_programs"] = programas
        
        logger.info(f"Found {len(programas)} relevant programs")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 3. INITIALIZE SESSION OBJECTS
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        memory = ConversationMemory(request.user_id)
        tracker = TrainingSessionTracker(session_id, request.user_id)
        pb = PromptBuilder()
                
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 4. BUILD PROMPT (INITIAL)
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        # Use initial prompt if no history, contextual if history exists
        if not memory.get_history():
            prompt = pb.build_initial_prompt(
                user_context=employee_ctx,
                ml_scores=rag_ctx.get("ml_scores")
            )
        else:
            prompt = pb.build_contextual_prompt(
                user_message=request.message,
                user_context=employee_ctx,
                rag_context=rag_ctx,
                history=memory.get_history(),
                ml_scores=rag_ctx.get("ml_scores")
            )
        
        logger.info("Prompt built, querying Gemini...")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 5. QUERY GEMINI
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        response_text = await client.query(prompt, memory.get_history())
        
        logger.info("Gemini response received")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 6. PARSE RESPONSE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                
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
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 7. UPDATE MEMORY
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        memory.add_turn("user", request.message)
        memory.add_turn("assistant", response_text)
        
        # Extract metadata from conversation
        metadata = memory.extract_metadata()
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 8. BUILD CHAT RESPONSE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
                
        recommendations = None
        if parsed.get("recommendations"): 
            recommendations = RecommendationData(
                course=parsed["recommendations"].get("course"),
                rationale=parsed["recommendations"].get("rationale"),
                plan_30_days=parsed["recommendations"].get("plan_30_days")
            )
        
        insights = parsed.get("insights", {})
        chat_response = ChatResponse(
            message=parsed.get("message", response_text),
            session_id=session_id,
            recommendations=recommendations,
            insights=InsightsData(
                general=insights.get("general", ""),
                department=insights.get("department", ""),
                personal=insights.get("personal", "")
            ),
            risk_alert=parsed.get("risk_alert")
        )
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 9. SAVE TO SUPABASE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
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
                "message": response_text,
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
        
            
# ═══════════════════════════════════════════════════════════════
# GET /api/v1/chat/history
# ═══════════════════════════════════════════════════════════════

@router.get("/chat/history", response_model=list[ChatTurn])
async def get_chat_history(
    user_id: str,
    limit: int = 10,
    supabase: Client = Depends(get_supabase_client)
) -> list[ChatTurn]:
    """
    Obtiene el historial de conversación de un empleado.
    
    Args:
        user_id: ID del empleado
        limit: Número máximo de turnos (default 10)
        supabase: Supabase client
    
    Returns:
        List[ChatTurn] ordenado por timestamp descendente
    """
    
    try:
        # Fetch último session
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
        
        turns = [
            ChatTurn(
                role=turn["role"],
                content=turn["message"],
                timestamp=turn["created_at"]
            )
            for turn in turns_response.data
        ]
        
        logger.info(f"Retrieved {len(turns)} turns for user {user_id}")
        return turns
    
    except Exception as e:
        logger.error(f"Error fetching chat history: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error retrieving chat history"
        )            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            
            