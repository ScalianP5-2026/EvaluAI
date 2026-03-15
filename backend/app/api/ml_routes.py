"""
ML Routes: Endpoints para ML scoring y NLP analysis.
POST /api/v1/ml/employee-scoring - Obtener scores ML del empleado
GET /api/v1/ml/nlp-analysis - Análisis NLP (placeholder)
"""

import logging
from typing import Dict, Optional

from app.services.ml_client import get_ml_client
from fastapi import APIRouter, HTTPException, status

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["ml"])


# ═══════════════════════════════════════════════════════════════
# POST /api/v1/ml/employee-scoring
# ═══════════════════════════════════════════════════════════════

@router.post("/ml/employee-scoring")
async def get_employee_scoring(profile: Dict[str, float]):
    """
    Obtiene scores ML para un empleado.
    
    Args:
        profile: Dict con {
            "motivation": float,
            "autoeficacia": float,
            "ai_usage": float,
            "edad": float,
            "antiguedad": float
        }
        
    Returns: 
        {
            "status": "success",
            "data": {
                "recommendation_score": 0.85,
                "risk_score": 0.12, 
                "course_affinity": {},
                "confidence": 0.89,
                "model_available": False
            }
        }
    """
    try:
        ml_client = get_ml_client()
        
        scores = ml_client.get_employee_scores(profile)
        
        logger.info("ML scoring completed successfully")
        
        return {
            "status": "success",
            "data": scores
        }
        
    except Exception as e:
        logger.error(f"Error in employee scoring: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing ML scoring"
        )

# ═══════════════════════════════════════════════════════════════
# GET /api/v1/ml/nlp-analysis
# ═══════════════════════════════════════════════════════════════

@router.get("/ml/nlp-analysis")
async def nlp_analysis(
    text: Optional[str] = None,
    analysis_type: str = "sentiment"
): 
    """
    Realiza análisis NLP (placeholder).
    
    Args:
        text: Texto a analizar
        analysis_type: Tipo de análisis (sentiment, topic, summary)
    
    Returns:
        {
            "status": "pending",
            "message": "NLP analysis coming soon"
        }
    """
    try:
        if not text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="text parameter required"
            )
        logger.info(f"NLP analysis requested: type={analysis_type}")
        
        # TODO: Implementar con pysentimiento/BERTopic
        return {
            "status": "pending",
            "message": "NLP analysis coming soon",
            "analysis_type": analysis_type
        }
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in NLP analysis: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error processing NLP analysis"
        )
    