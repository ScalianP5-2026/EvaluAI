"""
Pydantic schemas para chatbot y KPIs.
"""

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, RootModel

# ═══════════════════════════════════════════════════════════════
# CHAT SCHEMAS
# ═══════════════════════════════════════════════════════════════

class ChatRequest(BaseModel):
    """ Request para el endpoint /api/v1/chat/query"""
    
    user_id: str = Field(..., description="ID del empleado (ej: 1XVWCBPH)")
    message: str = Field(..., description="Mensaje del usuario")
    employee_context: Optional[Dict] = Field(
        default=None, 
        description="Contexto del empleado (si no viene, se fetch de BD)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "user_id": "1XVWCBPH",
                "message": "Quiero aprender Machine Learning",
                "employee_context": None
            }
        }

class RecommendationData(BaseModel):
    """Recomendaciones dentro de ChatResponse"""        
    
    course: Optional[str] = Field(default=None, description="Curso recomendado")
    rationale: Optional[str] = Field(default=None, description="Por qué este curso")
    plan_30_days: Optional[List[str]] = Field(
        default=None,
        description="Plan desglosado por semana"
    )

class InsightsData(BaseModel):
    """Insights en 3 niveles"""    
    
    general: str = Field(..., description="Insight a nivel empresa")
    department: str = Field(..., description="Insight del departamento")
    personal: str = Field(..., description="Insight personalizado")


class ChatResponse(BaseModel):
    """Response del endpoint /api/v1/chat/query"""
    
    message: str = Field(..., description="Respuesta natural del chatbot")
    session_id: str = Field(..., description="ID de sesión")
    recommendations: Optional[RecommendationData] = Field(
        default=None,
        description="Recomendacion (si la hay)"
    )
    insights: InsightsData = Field(..., description="Feedback en 3 niveles")
    risk_alert: Optional[str] = Field(
        default=None, 
        description="Alerta de riesgo (ej: dependencia_alta, baja_motivacion)"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Perfecto, veo que quieres aprender ML...",
                "session_id": "550e8400-e29b-41d4-a716-446655440000",
                "recommendations": {
                    "course": "ML Masterclass",
                    "rationale": "Ideal para tu nivel intermedio",
                    "plan_30_days": [
                        "Semana 1: Fundamentos de ML",
                        "Semana 2: Modelos supervisados",
                        "Semana 3: Evaluación y validación",
                        "Semana 4: Proyecto final"
                    ]
                },
                "insights": {
                    "general": "72% de empleados completan cuando empiezan...",
                    "department": "En tech mejoran 25% autoeficacia...",
                    "personal": "Basándome en tu perfil..."
                },
                "risk_alert": None
            }
        }

class ConversationHistoryRequest(BaseModel):
    """Request para GET /api/v1/chat/history"""
    
    user_id: str = Field(..., description="ID del empleado")
    limit: int = Field(default=10, ge=1, le=100, description="Últimos N turnos")
    
class ChatTurn(BaseModel):
    """Un turno de conversación"""
    
    role: str = Field(..., description="user o assistant")
    content: str = Field(..., description="Contenido del mensaje")
    timestamp: datetime = Field(default_factory=datetime.utcnow)

# ═══════════════════════════════════════════════════════════════
# KPI SCHEMAS
# ═══════════════════════════════════════════════════════════════

class AcceptanceDistribution(BaseModel):
    """KPI 1: Distribución de aceptación tecnológica"""
    very_low: int = Field(..., description="% muy baja aceptación")
    low: int = Field(..., description="% baja aceptación")
    medium: int = Field(..., description="% media aceptación")
    high: int = Field(..., description="% alta aceptación")
    very_high: int = Field(..., description="% muy alta aceptación")

class AIUsageCorrelation(BaseModel):
    """KPI 2: Correlación uso IA vs autoeficacia"""
    correlation: float = Field(..., description="Coeficiente Pearson")
    p_value: float = Field(..., description="P-value de significancia")
    significance: str = Field(..., description="Texto interpretable (ej: p < 0.001)")
    insight: str = Field(..., description="Insight generado")    
        
class DependencyRiskDistribution(BaseModel):
    """KPI 3: Distribución de riesgo de dependencia"""
    high_risk: int = Field(..., description="% alto riesgo")
    medium_risk: int = Field(..., description="% riesgo medio")
    low_risk: int = Field(..., description="% bajo riesgo")        
        
class DepartmentMetrics(BaseModel):
    """Métricas de un departamento"""
    avg_motivation: float = Field(..., description="Promedio motivación")
    avg_autoeficacia: float = Field(..., description="Promedio autoeficacia")
    count: int = Field(..., description="Número de empleados")
        


class DepartmentSegmentation(RootModel[Dict[str, DepartmentMetrics]]):
    """KPI 4: Segmentación por departamento"""
    
    root: Dict[str, DepartmentMetrics]

class MotivationByUsage(BaseModel):
    """Motivación en un nivel de uso"""
    
    avg_motivation: float = Field(..., description="Promedio motivación")
    count: int = Field(..., description="Número de empleados")
    

class MotivationByAIUsage(RootModel[Dict[str, MotivationByUsage]]):
    """KPI 5: Motivación cruzada por uso de IA"""   
    
    root: Dict[str, MotivationByUsage]
    
    
class KPIResponse(BaseModel):
    """Response del endpoint GET /api/v1/kpi/summary"""
    
    acceptance_distribution: AcceptanceDistribution = Field(
        ...,
        description="KPI 1: Distribución aceptación tecnológica"
    )
    ai_usage_correlation: AIUsageCorrelation = Field(
        ...,
        description="KPI 2: Correlación uso IA vs autoeficacia"
    )
    dependency_risk: DependencyRiskDistribution = Field(
        ...,
        description="KPI 3: Riesgo de dependencia"
    )
    department_segmentation: Dict[str, DepartmentMetrics] = Field(
        ...,
        description="KPI 4: Segmentación por departamento"
    )
    motivation_by_usage: Dict[str, MotivationByUsage] = Field(
        ...,
        description="KPI 5: Motivación vs uso de IA"
    )
    calculated_at: datetime = Field(
        default_factory=datetime.utcnow,
        description="Fecha/hora del cálculo"
    )
    
    class Config:
        json_schema_extra = {
            "example":{
                "acceptance_distribution": {
                    "very_low": 15,
                    "low": 20,
                    "medium": 35,
                    "high": 25,
                    "very_high": 5
                },
                "ai_usage_correlation": {
                    "correlation": 0.65,
                    "p_value": 0.001,
                    "significance": "p < 0.001",
                    "insight": "Uso de IA correlaciona positivamente con autoeficacia"
                },
                "dependency_risk": {
                    "high_risk": 15,
                    "medium_risk": 35,
                    "low_risk": 50
                },
                "department_segmentation": {
                    "Technology": {
                        "avg_motivation": 7.8,
                        "avg_autoeficacia": 7.6,
                        "count": 32
                    },
                    "Operations": {
                        "avg_motivation": 6.5,
                        "avg_autoeficacia": 6.2,
                        "count": 25
                    }
                },
                "motivation_by_usage": {
                    "1_never": {"avg_motivation": 3.2, "count": 10},
                    "2_rare": {"avg_motivation": 4.5, "count": 15},
                    "3_sometimes": {"avg_motivation": 5.8, "count": 25},
                    "4_frequent": {"avg_motivation": 7.2, "count": 30},
                    "5_very_frequent": {"avg_motivation": 8.1, "count": 20}
                },
                "calculated_at": "2026-03-05T10:30:00"
                
            }
        }


class ErrorResponse(BaseModel):
    """Response de error estándar"""        
    
    detail: str = Field(..., description="Mensaje de error")
    status_code: int = Field(..., description="Código HTTP")
    timestamp: datetime = Field(default_factory=datetime.utcnow)
        
        
        
        
        
        
        
        
        
        
        
        
        
        
        