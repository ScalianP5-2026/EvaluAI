""" 
ML Integration Client.
Maneja carga de modelos, scoring y analisis NLP.
"""

import logging
from pathlib import Path
from typing import Dict, Optional

import joblib
import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class MLClient:
    """Wrapper para cargar todos los modelos ML (.pkl) de la carpeta correcta y vectorizar peticiones."""
    
    def __init__(self):
        # Ajustado el path para apuntar a backend/ml/models (donde realmente están)
        self.models_dir = Path(__file__).resolve().parent.parent.parent / "ml" / "models"
        self.models = {}
        self._load_models()
    
    def _load_models(self):
        """Carga los 4 modelos oficiales y seguros."""
        
        files_to_load = {
            "dropout_risk": "dropout_risk_model_clean.pkl",
            "composite_roi": "composite_roi_model.pkl",
            "dependency": "dependency_multiclass_model.pkl",
            "motivation": "motivation_score_model.pkl"
        }      
          
        for key, filename in files_to_load.items():
            path = self.models_dir / filename
            if path.exists():
                try:
                    with open(path, 'rb') as f:
                        self.models[key] = joblib.load(f)
                    logger.info(f"✓ {key} model loaded")
                except Exception as e:
                    logger.warning(f"⚠ {key} model load failed: {e}")
            else:
                logger.warning(f"⚠ Model file not found: {path}")

    def get_employee_scores(self, profile: Dict) -> Dict:
        """
        Obtiene predicciones usando los 4 modelos cargados.
        """
        
        if not self.models:
            logger.warning("No models loaded, returning default scores")
            return self._zero_scores()
            
        try:
            # Vectorizar con la estructura real esperada (28 columnas)
            X_df = self._vectorize_profile(profile)
            
            # Inicializar los resultados 
            results = {
                "model_available": True,
                "confidence": 0.85 # CV average
            }
            
            # 1. Riesgo de abandono (Clasificador 1/0)
            if "dropout_risk" in self.models:
                # Predict_proba[0][1] devuelve la probabilidad real (0.0 a 1.0) de la clase POSITIVA (abandono)
                prob = self.models["dropout_risk"].predict_proba(X_df)[0][1]
                results["risk_score"] = float(prob)
            else:
                results["risk_score"] = 0.5
            
            # 2. ROI (Composite Regressor)
            if "composite_roi" in self.models:
                roi = self.models["composite_roi"].predict(X_df)[0]
                results["recommendation_score"] = float(roi) # Usado como recomendacion general
            else:
                results["recommendation_score"] = 5.0

            # 3. Predictor de Motivación futura
            if "motivation" in self.models:
                mot = self.models["motivation"].predict(X_df)[0]
                results["predicted_motivation"] = float(mot)

            # 4. Multiclase Dependencia
            if "dependency" in self.models:
                # Las clases son 'low', 'medium', 'high'
                dep_class = self.models["dependency"].predict(X_df)[0]
                results["dependency_prediction"] = str(dep_class)
                
            return results         
        
        except Exception as e:
            logger.error(f"Error getting ML scores: {e}")
            return self._zero_scores()

    
    def _zero_scores(self) -> Dict:
        return {
            "recommendation_score": 0.0,
            "risk_score": 0.0,
            "predicted_motivation": 0.0,
            "dependency_prediction": "unknown",
            "confidence": 0.0,
            "model_available": False
        }

    def _vectorize_profile(self, profile: Dict) -> pd.DataFrame:
        """
        Convierte profile dict a un vector compatible con las 28 variables esperadas.
        Si la UI no los envía, mapeamos con promedios neutrales de relleno.
        """
        
        # Mapeando datos reales desde UI / Data Manager si existen
        row = {
            # Demográficos y básicos numéricos
            "edad": profile.get("edad", profile.get("age", 35)),
            "antiguedad_empresa": profile.get("antiguedad_empresa", profile.get("years_in_company", 5)),
            "rol_tecnico": profile.get("rol_tecnico", 0), # Default no tecnico
            
            # IA Features directas del front o BD
            "frecuencia_uso_ia": profile.get("ai_usage", profile.get("ai_usage_frequency", 3)),
            "usa_chatgpt": 1 if profile.get("primary_tool") == "ChatGPT" else 0,
            "usa_gemini": 1 if profile.get("primary_tool") == "Gemini" else 0,
            "usa_copilot": 1 if profile.get("primary_tool") == "Copilot" else 0,
            "usa_lms_ia": 1 if profile.get("primary_tool") == "LMS IA" else 0,
            "usa_otra_ia": 1 if profile.get("primary_tool") == "Otra" else 0,
            "prefiere_humano_vs_ia": 3, # Valor medio ponderado temporal
            "nivel_integracion_ia": 3,
            
            # Categóricas (One-Hot Encoded) defaults a 0 (Unknown en este entorno)
            "genero_Mujer": 1 if profile.get("gender") == "Mujer" else 0,
            "genero_No binario": 0,
            "genero_Prefiero no decirlo": 0,
            "departamento_IT": 1 if profile.get("department") == "IT" else 0,
            "departamento_Marketing": 1 if profile.get("department") == "Marketing" else 0,
            "departamento_Operaciones": 1 if profile.get("department") == "Operaciones" else 0,
            "departamento_RRHH": 1 if profile.get("department") == "RRHH" else 0,
            "sector_Industria": 0,
            "sector_Servicios": 1 if profile.get("department") not in ["IT", "Operaciones"] else 0,
            "sector_Tecnología": 1 if profile.get("department") == "IT" else 0,
            "nivel_educativo_FP Superior": 1 if profile.get("education_level") == "FP Superior" else 0,            "nivel_educativo_Grado": 1 if profile.get("education_level") == "Grado" else 0,
            "nivel_educativo_Máster": 1 if profile.get("education_level") == "Máster" or profile.get("education_level") == "Master" else 0,
            "herramienta_principal_Copilot": 1 if profile.get("primary_tool") == "Copilot" else 0,
            "herramienta_principal_Gemini": 1 if profile.get("primary_tool") == "Gemini" else 0,
            "herramienta_principal_LMS IA": 1 if profile.get("primary_tool") == "LMS IA" else 0,
            "herramienta_principal_Otra": 1 if profile.get("primary_tool") == "Otra" else 0
        }
        
        # Devolver DataFrame asegurando el orden en que entrenamos:
        columns = list(row.keys()) # Están definidas en el orden perfecto de arriba
        df = pd.DataFrame([row])
        return df
    
    # Instancia Singleton
_ml_client_instance = None

def get_ml_client() -> MLClient:
    """Retorna una instancia única (singleton) del cliente ML."""
    global _ml_client_instance
    if _ml_client_instance is None:
        _ml_client_instance = MLClient()
    return _ml_client_instance