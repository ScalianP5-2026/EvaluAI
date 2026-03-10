"""
Survey Upload Schema - Pydantic models for CSV upload validation.

Validates employee survey data matching the Supabase employees table schema.
Supports the 41-column EIPIA CSV format but maps to 9 table columns.
"""

from typing import Optional

from pydantic import BaseModel, Field, field_validator


class EmployeeSurveyRow(BaseModel):
    """
    Pydantic model for validating a single survey row.
    Maps CSV columns to Supabase employees table columns.
    
    All fields are Optional to allow partial uploads and handle missing data gracefully.
    """
    
    # Primary identifier (required in practice, but optional in validation to collect errors)
    id_empleado: Optional[str] = Field(None, alias="id_empleado", description="Employee ID")
    
    # Demographic fields
    edad: Optional[int] = Field(None, ge=1, le=120, description="Age in years")
    genero: Optional[str] = Field(None, description="Gender")
    departamento: Optional[str] = Field(None, description="Department")
    antiguedad_empresa: Optional[int] = Field(None, ge=0, description="Years in company")
    nivel_educativo: Optional[str] = Field(None, description="Education level")
    
    # Technical & organizational
    rol_tecnico: Optional[int] = Field(None, description="Technical role (0/1)")
    sector: Optional[str] = Field(None, description="Sector")
    
    # AI usage (informational, not stored in employees table currently)
    frecuencia_uso_ia: Optional[int] = Field(None, ge=0, le=5, description="AI usage frequency")
    usa_chatgpt: Optional[int] = Field(None, ge=0, le=1, description="Uses ChatGPT (0/1)")
    usa_gemini: Optional[int] = Field(None, ge=0, le=1, description="Uses Gemini (0/1)")
    usa_copilot: Optional[int] = Field(None, ge=0, le=1, description="Uses Copilot (0/1)")
    
    # Survey scales (not stored in employees table currently)
    # Acceptance scales (AT1-AT4)
    AT1_rendimiento: Optional[float] = Field(None, ge=0, le=5)
    AT2_facilita_aprendizaje: Optional[float] = Field(None, ge=0, le=5)
    AT3_facilidad_uso: Optional[float] = Field(None, ge=0, le=5)
    AT4_integracion_positiva: Optional[float] = Field(None, ge=0, le=5)
    
    # Efficacy scales (AE1-AE4)
    AE1_resolver_problemas: Optional[float] = Field(None, ge=0, le=5)
    AE2_confianza_digital: Optional[float] = Field(None, ge=0, le=5)
    AE3_uso_eficaz: Optional[float] = Field(None, ge=0, le=5)
    AE4_seguridad_aplicacion: Optional[float] = Field(None, ge=0, le=5)
    
    # Motivation scales (M1-M4)
    M1_estimulante: Optional[float] = Field(None, ge=0, le=5)
    M2_aumenta_interes: Optional[float] = Field(None, ge=0, le=5)
    M3_aporta_valor: Optional[float] = Field(None, ge=0, le=5)
    M4_mayor_esfuerzo: Optional[float] = Field(None, ge=0, le=5)
    
    # Engagement scales (E1-E4)
    E1_adaptacion: Optional[float] = Field(None, ge=0, le=5)
    E2_feedback_util: Optional[float] = Field(None, ge=0, le=5)
    E3_aplicable_trabajo: Optional[float] = Field(None, ge=0, le=5)
    E4_aprendizaje_ritmo: Optional[float] = Field(None, ge=0, le=5)
    
    # Development scales (D1-D4)
    D1_mejora_competencias: Optional[float] = Field(None, ge=0, le=5)
    D2_preparado_retos: Optional[float] = Field(None, ge=0, le=5)
    D3_amplia_habilidades: Optional[float] = Field(None, ge=0, le=5)
    D4_aprendizaje_autonomo: Optional[float] = Field(None, ge=0, le=5)
    
    # Confidence scales (C1-C4)
    C1_confio_sin_verificar: Optional[float] = Field(None, ge=0, le=5)
    C2_dificil_sin_ia: Optional[float] = Field(None, ge=0, le=5)
    C3_pensamiento_critico: Optional[float] = Field(None, ge=0, le=5)
    C4_reflexiono_calidad: Optional[float] = Field(None, ge=0, le=5)
    
    # Additional CSV fields
    usa_lms_ia: Optional[int] = Field(None, ge=0, le=1)
    usa_otra_ia: Optional[int] = Field(None, ge=0, le=1)
    herramienta_principal: Optional[str] = Field(None)
    prefiere_humano_vs_ia: Optional[int] = Field(None, ge=0, le=5)
    nivel_integracion_ia: Optional[int] = Field(None, ge=0, le=5)
    
    class Config:
        """Pydantic config for flexible field matching."""
        # Allow population by field name
        populate_by_name = True
        # Allow extra fields (CSV might have more columns)
        extra = "allow"
    
    @field_validator("*", mode="before")
    @classmethod
    def strip_whitespace(cls, v):
        """Strip whitespace from string fields."""
        if isinstance(v, str):
            return v.strip() if v else None
        return v
    
    @field_validator("edad", "antiguedad_empresa", "rol_tecnico", mode="before", check_fields=False)
    @classmethod
    def convert_to_int(cls, v):
        """Convert numeric strings to integers."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return int(float(v.replace(",", ".")))
            except (ValueError, AttributeError):
                return None
        return v
    
    @field_validator(
        "AT1_rendimiento", "AT2_facilita_aprendizaje", "AT3_facilidad_uso", "AT4_integracion_positiva",
        "AE1_resolver_problemas", "AE2_confianza_digital", "AE3_uso_eficaz", "AE4_seguridad_aplicacion",
        "M1_estimulante", "M2_aumenta_interes", "M3_aporta_valor", "M4_mayor_esfuerzo",
        "E1_adaptacion", "E2_feedback_util", "E3_aplicable_trabajo", "E4_aprendizaje_ritmo",
        "D1_mejora_competencias", "D2_preparado_retos", "D3_amplia_habilidades", "D4_aprendizaje_autonomo",
        "C1_confio_sin_verificar", "C2_dificil_sin_ia", "C3_pensamiento_critico", "C4_reflexiono_calidad",
        "frecuencia_uso_ia", "prefiere_humano_vs_ia", "nivel_integracion_ia",
        mode="before", check_fields=False
    )
    @classmethod
    def convert_to_float(cls, v):
        """Convert numeric strings to floats."""
        if v is None or v == "":
            return None
        if isinstance(v, str):
            try:
                return float(v.replace(",", "."))
            except (ValueError, AttributeError):
                return None
        return v
    
    def to_supabase_employee(self) -> dict:
        """
        Map validated row to Supabase employees table columns.
        
        Returns only the 9 columns that the employees table supports.
        """
        return {
            "employee_id": self.id_empleado,
            "age": self.edad,
            "gender": self.genero,
            "department": self.departamento,
            "years_in_company": self.antiguedad_empresa,
            "education_level": self.nivel_educativo,
            "technical_role": self.rol_tecnico,
            "sector": self.sector,
        }


class SurveyUploadResponse(BaseModel):
    """Response model for CSV upload endpoint."""
    total_rows: int = Field(..., description="Total rows in CSV")
    valid_rows: int = Field(..., description="Rows that passed validation")
    invalid_rows: int = Field(..., description="Rows that failed validation")
    inserted_rows: int = Field(..., description="Rows successfully inserted")
    skipped_duplicates: int = Field(..., description="Rows skipped due to duplicate employee_id")
    errors: list[dict] = Field(default_factory=list, description="Validation errors (first 10)")


class SurveyUploadError(BaseModel):
    """Model for individual row errors."""
    row: int = Field(..., description="CSV row number (1-indexed)")
    error: str = Field(..., description="Error message")
