"""
KPI Engine: Calcula 5 KPIs MVP desde CSV.
"""

import logging
from pathlib import Path
from typing import Dict

import numpy as np
import pandas as pd
from scipy.stats import pearsonr

import os
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

# Ruta al dataset (obtenida directamente desde .env EVALUAI_SURVEYS_PATH)
DATA_PATH = Path(os.getenv("EVALUAI_SURVEYS_PATH", "data/raw/EIPIA_FO_dataset_100_personas.csv"))


class KPIEngine:
    """Calcula KPIs MVP."""
    
    def __init__(self):
        """Load dataset on init."""
        try:
            if not DATA_PATH.exists():
                raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
            self.df = pd.read_csv(DATA_PATH, sep=';')
            logger.info(f"Loaded {len(self.df)} employees from dataset: {DATA_PATH}")
        except Exception as e:
            logger.error(f"Error loading dataset: {e}")
            self.df = pd.DataFrame()
            
    def calculate_acceptance_distribution(self) -> Dict:
        """
        Distribución de Aceptación Tecnológica (AT1-AT4).
        
        Returns:
            {"very_low": 15, "low": 20, "medium": 35, "high": 25, "very_high": 5}
        """
        try:
            # Línea ~38 - buscar "at" columns
            at_cols = [col for col in self.df.columns if col.startswith("AT")]  # ✅ UPPERCASE

            # etc para todas las búsquedas de columnas
            if not at_cols:
                logger.warning("AT columns not found")
                return {}
            
            # Media AT
            self.df["at_mean"] = self.df[at_cols].mean(axis=1)
            
            # Distribución 
            bins = [0, 2, 4, 5, 6, 7]
            labels = ["very_low", "low", "medium", "high", "very_high"]
            distribution = pd.cut(self.df["at_mean"], bins=bins, labels=labels).value_counts(normalize=True).to_dict()
            
            # Convert a %
            distribution = {k: int(v * 100) for k, v in distribution.items()}
            logger.info(f"Acceptance distribution: {distribution}")
            return distribution
        
        except Exception as e:
            logger.error(f"Error calculating acceptance: {e}")
            return {}
    
    def calculate_ai_usage_vs_autoeficacia_correlation(self) -> Dict:
        """ 
        Correlacion entre uso de IA y autoeficacia. 
        
        Returns:
            {
                "correlation": 0.65,
                "p_value": 0.001,
                "significance": "p < 0.001",
                "insight": "..."
            }
        """
        try: 
            # Detectar columnas
            freq_cols = [col for col in self.df.columns if "frecuencia" in col.lower()]
            ae_cols = [col for col in self.df.columns if col.startswith("AE")]
            
            if not freq_cols or not ae_cols:
                logger.warning("Required columns not found")
                return {}
            
            # Promedios
            self.df["ai_frequency"] = self.df[freq_cols[0]]
            self.df["autoeficacia"] = self.df[ae_cols].mean(axis=1)
            
            # Pearson
            corr, p_value = pearsonr(self.df["ai_frequency"], self.df["autoeficacia"])
            
            significance = "p < 0.001" if p_value < 0.001 else f"p = {p_value:.3f}"
            
            result = {
                "correlation": round(corr, 2), 
                "p_value": round(p_value, 4),
                "significance": significance,
                "insight": "Uso de IA correlaciona positivamente con autoeficacia" if corr > 0.3 else "Baja correlación"
            }
            
            logger.info(f"AI usage vs autoeficacia correlation: {corr}")
            return result

        except Exception as e:
            logger.error(f"Error calculating correlation: {e}")
            return {}
        
    def calculate_dependency_risk_distribution(self) -> Dict:
        """
        Distribución de riesgo de dependencia (escala C).
        C3 y C4 se invierten antes.
        
        Returns:
            {"high_risk": 15, "medium_risk": 35, "low_risk": 50}
        """
        try: 
            c_cols = [col for col in self.df.columns if col.startswith("C")]
            if len(c_cols) < 4:
                logger.warning("C columns not found (need c1, c2, c3, c4)")
                return {}
            
            # Copiar para no modificar original
            df_temp = self.df.copy()
            
            # Invertir C3 y C4 
            if c_cols[2] in df_temp.columns:
                df_temp[c_cols[2]] = 8 - df_temp[c_cols[2]]
            if c_cols[3] in df_temp.columns:
                df_temp[c_cols[3]] = 8 - df_temp[c_cols[3]]
                
            # Media
            df_temp["dependency_risk"] = df_temp[c_cols].mean(axis=1)
            
            # Categorizar
            high = (df_temp["dependency_risk"] > 5.5).sum() / len(df_temp) * 100
            medium = ((df_temp["dependency_risk"] > 3.5) & (df_temp["dependency_risk"] <= 5.5)).sum() / len(df_temp) * 100
            low = (df_temp["dependency_risk"] <= 3.5).sum() / len(df_temp) * 100
            
            result = {
                "high_risk": int(high),
                "medium_risk": int(medium),
                "low_risk": int(low)
            }
            
            logger.info(f"Dependency risk distribution: {result}")
            return result
        
        except Exception as e:
            logger.error(f"Error calculating dependency risk: {e}")
            return {}
    
    def calculate_department_segmentation(self) -> Dict:
        """
        KPI por departamento.
        
        Returns:
            {
                 "Technology": {"avg_motivation": 7.8, "avg_autoeficacia": 7.6, "count": 32},
                ...
            }
        """
        try:
            dept_col = [col for col in self.df.columns if "departamento" in col.lower()]
            m_cols = [col for col in self.df.columns if col.startswith("M")]
            ae_cols = [col for col in self.df.columns if col.startswith("AE")]
            
            if not dept_col or not m_cols or not ae_cols:
                logger.warning("Required columns not found")
                return {}
            
            dept_col = dept_col[0]
            
            self.df["motivation"] = self.df[m_cols].mean(axis=1)
            self.df["autoeficacia"] = self.df[ae_cols].mean(axis=1)
            
            grouped = self.df.groupby(dept_col).agg({
                "motivation": "mean",
                "autoeficacia": "mean",
                dept_col: "count"
            }).rename(columns={dept_col: "count"})
            
            result = {}
            for dept, row in grouped.iterrows():
                result[dept] = {
                    "avg_motivation": round(row["motivation"], 2),
                    "avg_autoeficacia": round(row["autoeficacia"], 2),
                    "count": int(row["count"])
                }
            
            logger.info(f"Department segmentation: {len(result)} departments")
            return result
        
        except Exception as e:
            logger.error(f"Error calculating department segmentation: {e}")
            return {}
        
    def calculate_motivation_by_ai_usage(self) -> Dict:
        """
        Motivacion cruzada por frecuencia de uso de IA.
        
        Returns:
            {
                "1_never": {"avg_motivation": 3.2, "count": 10},
                ...
            }
        """
        try:
            freq_cols = [col for col in self.df.columns if "frecuencia" in col.lower()]
            m_cols = [col for col in self.df.columns if col.startswith("M")]
            
            if not freq_cols or not m_cols:
                logger.warning("Required columns not found")
                return {}
            
            freq_col = freq_cols[0]
            
            self.df["motivation"] = self.df[m_cols].mean(axis=1)
            
            grouped = self.df.groupby(freq_col).agg({
                "motivation": ["mean", "count"]
            })
            
            result = {}
            labels = ["1_never", "2_rare", "3_sometimes", "4_frequent", "5_very_frequent"]
            
            for idx, (freq, row) in enumerate(grouped.iterrows()):
                if idx < len(labels):
                    result[labels[idx]] = {
                        "avg_motivation": round(float(row[("motivation", "mean")]), 2),
                        "count": int(row[("motivation", "count")])
                    }
                    
            logger.info(f"Motivation by AI usage: {len(result)} segments")
            return result
        
        except Exception as e:
            logger.error(f"Error calculating motivation by usage: {e}")
            return {}
        
# Funciones standalone (mas facil de usar en routes)

_engine = None

def get_kpi_engine() -> KPIEngine:
    global _engine
    if _engine is None:
        _engine = KPIEngine()
    return _engine

def calculate_acceptance_distribution() -> Dict:
    return get_kpi_engine().calculate_acceptance_distribution()

def calculate_ai_usage_vs_autoeficacia_correlation() -> Dict:
    return get_kpi_engine().calculate_ai_usage_vs_autoeficacia_correlation()

def calculate_dependency_risk_distribution() -> Dict:
    return get_kpi_engine().calculate_dependency_risk_distribution()

def calculate_department_segmentation() -> Dict:
    return get_kpi_engine().calculate_department_segmentation()

def calculate_motivation_by_ai_usage() -> Dict:
    return get_kpi_engine().calculate_motivation_by_ai_usage()

    