""" 
ML Integration Client.
Maneja carga de modelos, scoring y analisis NLP.
"""

import logging
import pickle
from pathlib import Path
from typing import Dict, List, Optional

import numpy as np

logger = logging.getLogger(__name__)


class MLClient:
    """Wrapper para modelos ML (.pkl files)"""
    
    def __init__(self):
        """Carga modelos al init"""
        self.models_dir = Path(__file__).parent.parent.parent / "models"
        self.rf_model = None
        self.scaler = None # Para normalización
        self.nlp_models = {}
        self._load_models()
    
    def _load_models(self):
        """Carga RandomForest cuando esté disponible"""
        rf_path = self.models_dir / "random_forest_model.pkl"
        
        if rf_path.exists():
            try:
                with open(rf_path, 'rb') as f:
                    self.rf_model = pickle.load(f)
                    # Espera dict: {"model": rf, "scaler": scaler, "feature_names": [...]}
                    if isinstance(model_data, dict):
                        self.rf_model = model_data.get("model")
                        self.scaler = model_data.get("scaler")
                    else:
                        self.rf_model = model_data # Legacy: solo el modelo
                logger.info("✓ RandomForest model loaded")
            except Exception as e:
                logger.warning(f"⚠ RF model load failed: {e}")
                self.rf_model = None
        else: 
            logger.warning(f"⚠ Model file not found: {rf_path}")
    
    def get_employee_scores(self, employee_profile: Dict) -> Optional[Dict]:
        """
        Obtiene scores ML para empleado.
        
        Si modelo no disponible, devuelve estructura con 0s.

        
        Args:
            employee_profile: {
                "motivation": 7.5,
                "autoeficacia": 8.0,
                "ai_usage": 3,
                "edad": 32,
                "angiguedad": 17
            }
        
        Returns: 
            {
                "recommendation_score": 0.85,
                "risk_score": 0.12,
                "course_affinity": {
                    "AWS": 0.92,
                    "Python": 0.78,
                    "ML": 0.65
                },
                "confidence": 0.89
                "model_available": True
            }
        """
        try:
            if not self.rf_model:
                logger.warning("RF model not loaded, returning None")
                return self._zero_scores()
        
            # Vectorizar profile
            X = self._vectorize_profile(employee_profile)
            
            # Normalizar si tenemos scaler
            if self.scaler:
                X = self.scaler.transform(X)
                
            # Predict
            scores = self.rf_model.predict(X)[0] # [0] si solo 1 empleado
            
            return {
                "recommendation_score": float(scores[0]),
                "risck_score": float(scores[1]) if len(scores) > 1 else 0.5,
                "course_affinity": self._map_scores_to_courses(scores),
                "confidence": self._calculate_confidence(scores), # Desde modelo
                "model_available": True
            }
        
        except Exception as e: 
            logger.error(f"Error getting ML scores: {e}")
            return self._zero_scores()
    
    def _zero_scores(self) -> Dict:
        """Estructura de scores cuando modelo no disponible"""
        return {
            "recommendation_score": 0.0,
            "risk_score": 0.0,
            "course_affinity": {},
            "confidence": 0.0,
            "model_available": False
        }
    
    def _vectorize_profile(self, profile: Dict) -> np.ndarray:
        """
        Convierte profile dict a vector para RF.
        
        ORDEN CRITICA: Debe coincidir exactamente con entrenamiento.
        """
        
        return np.array([[
            profile.get("motivation", 0.0),
            profile.get("autoeficacia", 0.0),
            profile.get("ai_usage", 0),
            profile.get("edad", 0),
            profile.get("antiguedad", 0)
        ]])
    
    def _map_scores_to_courses(self, scores: np.ndarray) -> Dict:
        """
        Mapea scores a cursos disponibles.
        
        TODO: @ML_TEAM - Implementar mapping real
        Actualmente retorna dict vacío (no hardcodeado).
        
        Debería:
        1. Cargar lista de cursos desde Supabase
        2. Normalizar scores a [0, 1]
        3. Mapear a afinity scores por curso
        """
        # PLACEHOLDER: Vacío hasta que se implemente
        return {}
    
    def _calculate_confidence(self, scores: np.ndarray) -> float:
        """
        Calcula confidence desde cross-validation del modelo.
        
        TODO: @ML_TEAM - Pasar CV score desde .pkl
        Actualmente: 0.0 (no hardcodeado a 0.89)
        """
        # PLACEHOLDER: Retorna 0 hasta que haya data real
        return 0.0


def get_ml_client() -> MLClient:
    """Singleton: devuelve instancia única"""
    global _ml_client
    if _ml_client is None:
        _ml_client = MLClient()
    return _ml_client


_ml_client = None