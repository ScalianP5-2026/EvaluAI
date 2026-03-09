"""
Main entry point for EvaluAI FastAPI application.
Initializes the app, configures routes, CORS, and startup/shutdown hooks.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat_routes, kpi_routes
from app.config import (
    AppConfig,
    close_supabase_client,
    get_supabase_client,
)
from app.database.seeds.courses_seed import seed_courses
from app.database.seeds.employees_seed import seed_employees

logger = logging.getLogger(__name__)

# ═══════════════════════════════════════════════════════════════
# Lifespan Context Manager (FastAPI 0.93+)
# ═══════════════════════════════════════════════════════════════

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Manage app startup and shutdown events.
    
    Startup:
        - Initialize Supabase client
        - Seed demo courses (if needed)
        - Log KPIs initialization status
    
    Shutdown:
        - Close Supabase connection
    """
    # ━━━━━━━━━━━━━━━━━ STARTUP ━━━━━━━━━━━━━━━━━
    logger.info("=== EvaluAI Backend Starting ===")
    
    try:
        # Initialize Supabase
        supabase = get_supabase_client()
        logger.info("✓ Supabase client initialized")
        
        # Seed demo courses (execute once on startup)
        try:
            logger.info("Seeding demo courses...")
            await seed_courses(supabase)
            logger.info("✓ Demo courses seeded successfully")
        except Exception as e:
            logger.warning(f"⚠ Demo courses seed skipped: {str(e)}")
        
        # Seed demo employees (execute once on startup)
        try:
            logger.info("Seeding demo employees...")
            await seed_employees(supabase)
            logger.info("✓ Demo employees seeded successfully")
        except Exception as e:
            logger.warning(f"⚠ Demo employees seed skipped: {str(e)}")
            
        logger.info("✓ API ready at /api/v1 (Gemini configured)")
        logger.info("=== EvaluAI Backend Ready ===")
        
    except Exception as e:
        logger.error(f"✗ Startup failed: {str(e)}")
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
    app.include_router(chat_routes.router)
    app.include_router(kpi_routes.router)
    
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
