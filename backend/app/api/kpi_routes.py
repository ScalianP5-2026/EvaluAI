"""
KPI Routes: Endpoints analiticos.
GET /api/v1/kpi/summary - Obtener resumen de 5 KPIs
"""

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from app.api.access_control import require_rrhh_access
from app.models.chat_schemas import KPIResponse
from app.services.kpi_engine import (
    calculate_acceptance_distribution,
    calculate_ai_usage_vs_autoeficacia_correlation,
    calculate_department_segmentation,
    calculate_dependency_risk_distribution,
    calculate_motivation_by_ai_usage,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1", tags=["kpi"])

# ═══════════════════════════════════════════════════════════════
# GET /api/v1/kpi/summary
# ═══════════════════════════════════════════════════════════════

@router.get("/kpi/summary", response_model=KPIResponse)
async def get_kpi_summary(
    _current_user=Depends(require_rrhh_access),
) -> KPIResponse:
    """
    Obtiene resumen de los 5 KPIs de MVP.
    
    Estos valores se calculan UNA SOLA VEZ al startup (caché de memoria).
    No requiere parámetros - usa el dataset cargado en kpi_engine.
    
    Returns: 
        KPIResponse con 5 KPIs calculados
    
    Raises:
        HTTPException 500 si hay error en cálculo
    """
    try:
        logger.info("Calculating KPI summary...")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # KPI 1: ACCEPTANCE DISTRIBUTION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        acceptance_dist = calculate_acceptance_distribution()
        if not acceptance_dist:
            raise ValueError("Failed to calculate acceptance distribution")
        
        logger.info(f"KPI1 Acceptance: {acceptance_dist}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # KPI 2: AI USAGE VS AUTOEFICACIA CORRELATION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        correlation = calculate_ai_usage_vs_autoeficacia_correlation()
        if not correlation:
            raise ValueError("Failed to calculate correlation")
        
        logger.info(f"KPI2 Correlation: r={correlation.get('correlation')}, p={correlation.get('p_value')}")

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # KPI 3: DEPENDENCY RISK DISTRIBUTION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        risk_dist = calculate_dependency_risk_distribution()
        if not risk_dist:
            raise ValueError("Failed to calculate dependency risk")
        
        logger.info(f"KPI3 Dependency Risk: {risk_dist}")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # KPI 4: DEPARTMENT SEGMENTATION
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        dept_seg = calculate_department_segmentation()
        if not dept_seg:
            raise ValueError("Failed to calculate department segmentation")
        
        logger.info(f"KPI4 Departments: {len(dept_seg)} departments segmented")
        
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # KPI 5: MOTIVATION BY AI USAGE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        motivation = calculate_motivation_by_ai_usage()
        if not motivation:
            raise ValueError("Failed to calculate motivation by AI usage")
        
        logger.info(f"KPI5 Motivation: {len(motivation)} segments")


        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # BUILD RESPONSE
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        
        kpi_response = KPIResponse(
            acceptance_distribution=acceptance_dist,
            ai_usage_correlation=correlation,
            dependency_risk=risk_dist,
            department_segmentation=dept_seg,
            motivation_by_usage=motivation
        )
        
        logger.info("KPI summary calculated successfully")
        return kpi_response
    
    except ValueError as e:
        logger.error(f"Validation error in KPI calculation: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"KPI calculation failed: {str(e)}"
        )
    except Exception as e:
        logger.error(f"Unexpected error in KPI summary: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error calculating KPI summary"
        )
