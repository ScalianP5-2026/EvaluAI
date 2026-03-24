"""
Tests de integración para los endpoints de Machine Learning y NLP.
Asegura que el contrato de entrada/salida (200 OK, 400 Bad Request) se mantenga.
"""

from app.main import app
from fastapi.testclient import TestClient

client = TestClient(app)

# ═══════════════════════════════════════════════════════════════
# Tests para POST /api/v1/ml/employee-scoring
# ═══════════════════════════════════════════════════════════════

def test_employee_scoring_success():
    """Prueba que el endpoint devuelva 200 OK con un payload válido."""
    payload = {
        "motivation": 8.5,
        "autoeficacia": 7.0,
        "ai_usage": 4.0,
        "edad": 35.0,
        "antiguedad": 5.0
    }
    
    response = client.post("/api/v1/ml/employee-scoring", json=payload)
    
    assert response.status_code == 200, "Should return 200 for a valid profile"
    
    data = response.json()
    assert data["status"] == "success"
    assert "recommendation_score" in data["data"]
    assert "risk_score" in data["data"]
    assert "confidence" in data["data"]

def test_employee_scoring_invalid_payload():
    """Prueba que el endpoint falle correctamente (422) si el body no es un dict válido."""
    # Enviamos una lista en lugar de un diccionario (Dict[str, float])
    response = client.post("/api/v1/ml/employee-scoring", json=["not", "a", "dict"])
    
    assert response.status_code == 422, "Should return Unprocessable Entity for invalid schema"


# ═══════════════════════════════════════════════════════════════
# Tests para GET /api/v1/ml/nlp-analysis
# ═══════════════════════════════════════════════════════════════

def test_nlp_analysis_success():
    """Prueba que el endpoint devuelva 200 (estado pending) enviando el text."""
    params = {
        "text": "El curso de Python me ha parecido excelente y muy útil.",
        "analysis_type": "sentiment"
    }
    
    response = client.get("/api/v1/ml/nlp-analysis", params=params)
    
    assert response.status_code == 200, "Should return 200 when 'text' parameter is provided"
    
    data = response.json()
    assert data["status"] == "pending"
    assert data["analysis_type"] == "sentiment"
    assert "NLP analysis coming soon" in data["message"]

def test_nlp_analysis_missing_text():
    """Prueba que el endpoint lance 400 Bad Request si no se envía el text."""
    # Omitimos el parámetro 'text'
    params = {
        "analysis_type": "sentiment"
    }
    
    response = client.get("/api/v1/ml/nlp-analysis", params=params)
    
    assert response.status_code == 400, "Should return 400 Bad Request when 'text' is missing"
    assert "text parameter required" in response.json()["detail"]