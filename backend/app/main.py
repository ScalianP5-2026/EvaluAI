"""
Main entry point for EvaluAI FastAPI application.
Initializes the app, configures routes, CORS, and startup/shutdown hooks.
"""

import logging
from contextlib import asynccontextmanager

from app.api import auth_routes, chat_routes, kpi_routes, ml_routes, surveys_routes
from app.config import (
    AppConfig,
    close_supabase_client,
    get_supabase_client,
)
from app.database.seeds.courses_seed import seed_courses
from app.database.seeds.employees_seed import seed_employees
from app.database.seeds.mentores_seed import seed_mentores
from app.database.seeds.user_credentials_seed import seed_user_credentials
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

try:
    from backend.routes.nlp_routes import router as nlp_router
except ImportError:
    from routes.nlp_routes import router as nlp_router

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Lifespan Context Manager (FastAPI 0.93+)
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    STARTUP: Ejecuta seeds
    """

    # ━━━━━━━━━━━━━━━━━ STARTUP ━━━━━━━━━━━━━━━━━
    logger.info("=== EvaluAI Backend Starting ===")
    
    try:
        # Initialize Supabase
        supabase = get_supabase_client()
        logger.info("✓ Supabase initialized")
        
        # Seed courses (execute once on startup)
        try:
            logger.info("Seeding courses...")
            await seed_courses(supabase)
            logger.info("✓ Courses seeded")
        except Exception as e:
            logger.warning(f"⚠ Courses seed failed: {e}")
        
        # Seed mentores
        try:
            logger.info("Seeding mentores...")
            await seed_mentores(supabase)
            logger.info("✓ Mentores seeded")
        except Exception as e:
            logger.warning(f"⚠ Mentores seed failed: {e}")

        # Seed employees (execute once on startup)
        try:
            logger.info("Seeding employees...")
            await seed_employees(supabase)
            logger.info("✓ Employees seeded")
        except Exception as e:
            logger.warning(f"⚠ Employees seed failed: {e}")

        # Seed user credentials (execute once on startup)
        try:
            logger.info("Seeding user credentials...")
            await seed_user_credentials(supabase)
            logger.info("✓ User credentials seeded successfully")
        except Exception as e:
            logger.warning(f"⚠ User credentials seed skipped: {str(e)}")
            
        logger.info("✓ API ready at /api/v1 (Gemini configured)")
        logger.info("=== EvaluAI Backend Ready ===")
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {e}")
        raise

    # ━━━━━━━━━━━━━━━━━ SHUTDOWN ━━━━━━━━━━━━━━━━
    try:
        yield
    finally:
        logger.info("=== EvaluAI Backend Shutting Down ===")
        close_supabase_client()
        logger.info("✓ Supabase client closed")
        logger.info("=== EvaluAI Backend Stopped ===")

# ═══════════════════════════════════════════════════════════════
# FastAPI Application Factory
# ═══════════════════════════════════════════════════════════════

def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        FastAPI: Configured application instance
    """
    # Initialize FastAPI with lifespan context
    app = FastAPI(
        title=AppConfig.TITLE,
        description=AppConfig.DESCRIPTION,
        version=AppConfig.VERSION,
        lifespan=lifespan
    )
    
    # ━━━━━━━━━━━━━━━━━ CORS Middleware ━━━━━━━━━━━━━━━━━
    app.add_middleware(
        CORSMiddleware,
        allow_origins=AppConfig.CORS_ORIGINS,
        allow_credentials=AppConfig.CORS_ALLOW_CREDENTIALS,
        allow_methods=AppConfig.CORS_ALLOW_METHODS,
        allow_headers=AppConfig.CORS_ALLOW_HEADERS,
    )
    
    # ━━━━━━━━━━━━━━━━━ Routes Registration ━━━━━━━━━━━━━━━━━
    app.include_router(auth_routes.router)
    app.include_router(chat_routes.router)
    app.include_router(kpi_routes.router)
    app.include_router(surveys_routes.router)
    app.include_router(ml_routes.router)
    app.include_router(nlp_router)
    
    # ━━━━━━━━━━━━━━━━━ Health Check Endpoints ━━━━━━━━━━━━━━━━━
    @app.get("/api/v1/health", tags=["health"])
    async def health_check():
        """Health check endpoint."""
        return {
            "status": "healthy",
            "service": "EvaluAI API",
            "version": AppConfig.VERSION
        }
    
    @app.get("/api/v1/config", tags=["health"])
    async def get_config():
        """Get API configuration (public info only)."""
        return {
            "api_version": AppConfig.VERSION,
            "gemini_model": AppConfig.GEMINI_MODEL,
            "gemini_retries": AppConfig.GEMINI_MAX_RETRIES,
            "max_conversation_turns": AppConfig.MAX_CONVERSATION_TURNS
        }
    
    # ━━━━━━━━━━━━━━━━━ Root Endpoint ━━━━━━━━━━━━━━━━━
    @app.get("/", tags=["info"])
    async def root():
        """Root endpoint with API documentation."""
        return {
            "message": "EvaluAI API - AI-powered training evaluation",
            "docs": "/docs",
            "version": AppConfig.VERSION,
            "endpoints": {
                "chat": "/api/v1/chat/query",
                "history": "/api/v1/chat/history",
                "kpi": "/api/v1/kpi/summary",
                "upload": "/api/v1/upload/surveys",
                "nlp_summary": "/api/nlp/summary",
                "nlp_executive": "/api/nlp/executive",
                "nlp_employee": "/api/nlp/employee/{employee_id}",
                "health": "/api/v1/health"
            }
        }
    
    return app

# ═══════════════════════════════════════════════════════════════
# Application Instance
# ═══════════════════════════════════════════════════════════════

app = create_app()

# ═══════════════════════════════════════════════════════════════
# Development Server (for local testing)
# ═══════════════════════════════════════════════════════════════

if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
