# EvaluAI

## 0) Overview / Visión

**ES**  
EvaluAI es un MVP para analizar el impacto de la formación apoyada por IA en empleados.  
Integra tres módulos: dashboard analítico, asistente de recomendación y análisis NLP de feedback.

**EN**  
EvaluAI is an MVP to analyze the impact of AI-assisted learning across employees.  
It combines three modules: analytics dashboard, recommendation assistant, and NLP feedback analysis.

## 1) Problem / Problema

**ES**  
EvaluAI ayuda a responder preguntas operativas de RRHH y L&D (Learning & Development):

1. Cómo se usa la IA en formación.
2. Si existe relación entre uso de IA y variables como motivación, autoeficacia o aceptación.
3. Qué acciones concretas conviene recomendar por perfil.
4. Qué patrones aparecen en comentarios cualitativos.

**EN**  
EvaluAI helps HR and L&D teams answer practical questions:

1. How AI is currently used in training.
2. Whether AI usage is related to motivation, self-efficacy, or acceptance.
3. Which concrete actions should be recommended per profile.
4. Which patterns emerge from qualitative feedback.

## 2) Core Capabilities / Capacidades

**ES**

1. Dashboard de analítica descriptiva.
2. Chatbot de recomendación formativa (cursos, mentor, plan de 30 días).
3. Analizador NLP de opiniones y sugerencias.

**EN**

1. Descriptive analytics dashboard.
2. Training recommendation chatbot (courses, mentor, 30-day plan).
3. NLP analyzer for comments and suggestions.

## 3) Architecture / Arquitectura

**ES**  
Arquitectura por capas:

```text
[React UI] ---> [FastAPI API] ---> [Services]
                               |--> analytics.py
                               |--> recommender.py
                               |--> nlp.py
                               '--> data_store.py

[Data files]
  - backend/data/raw/survey_raw.xlsx
  - backend/data/courses.csv
  - backend/data/mentors.csv
```

Componentes:

1. Presentación  
- `frontend/` (React + Vite).
2. API  
- `backend/app/main.py` (bootstrap FastAPI + CORS + health).  
- `backend/app/api/routes.py` (endpoints `/api/v1`).
3. Dominio  
- `backend/app/services/analytics.py`.  
- `backend/app/services/recommender.py`.  
- `backend/app/services/nlp.py`.
4. Datos  
- `backend/app/services/data_store.py` (carga, normalización y caché).

**EN**  
Layered architecture:

```text
[React UI] ---> [FastAPI API] ---> [Services]
                               |--> analytics.py
                               |--> recommender.py
                               |--> nlp.py
                               '--> data_store.py

[Data files]
  - backend/data/raw/survey_raw.xlsx
  - backend/data/courses.csv
  - backend/data/mentors.csv
```

Components:

1. Presentation  
- `frontend/` (React + Vite).
2. API  
- `backend/app/main.py` (FastAPI bootstrap + CORS + health).  
- `backend/app/api/routes.py` (`/api/v1` routes).
3. Domain  
- `backend/app/services/analytics.py`.  
- `backend/app/services/recommender.py`.  
- `backend/app/services/nlp.py`.
4. Data  
- `backend/app/services/data_store.py` (loading, normalization, cache).

## 4) Functional Flow / Flujo funcional

**ES**

1. al arrancar carga en memoria ( en una instancia `DataRepository`) los 3 .csv en backend\data (encuestas, cursos y mentores) para no leer continuamente de csv´s.
2. React consume la API.
3. Si se sube un CSV (`/surveys/upload`), la API valida, parsea, normaliza y reemplaza el dataset de encuestas en memoria.
4. Dashboard (`/dashboard/summary`) calcula métricas, distribución, correlaciones e insights.
5. Chat (`/chat/query`) cruza el objetivo del empleado con tags de cursos y expertise de mentores, y estima mejora para perfiles similares.
6. NLP (`/nlp/analyze`) tokeniza comentarios, calcula sentimiento, detecta temas y propone recomendaciones grupales.

**EN**

1. `DataRepository` loads surveys, courses, and mentors at startup.
2. React calls the API.
3. If a CSV is uploaded (`/surveys/upload`), the API validates, parses, normalizes, and replaces the in-memory dataset.
4. Dashboard (`/dashboard/summary`) computes metrics, distribution, correlations, and insights.
5. Chat (`/chat/query`) matches learning goals against course tags and mentor expertise, then estimates improvement for similar profiles.
6. NLP (`/nlp/analyze`) tokenizes comments, computes sentiment, detects topics, and proposes group recommendations.

## 5) Data Model / Modelo de datos

**ES**

Dataset principal:

- Archivo: `backend/data/raw/survey_raw.xlsx`
- Grano: 1 fila = 1 respuesta
- Incluye: perfil, uso de IA, índices, bloque Likert, feedback cualitativo

Normalización interna (backend):

- Campos normalizados principales: `employee_id`, `role`, `motivation`, `ai_usage`, `self_efficacy`, `talent_development`, `experience_years`, `acceptance`, `open_experience_ai_learning`, `open_challenges_ai_usage`, `open_training_needs`
- Campos de compatibilidad heredados aún presentes en backend: `comment`, `last_goal` (se rellenan a partir de los campos abiertos anteriores para mantener compatibilidad con el esquema legado)
- `ai_usage` normalizado a: `never`, `rarely`, `sometimes`, `frequently`, `always`

**EN**

Main dataset:

- File: `backend/data/raw/survey_raw.xlsx`
- Grain: 1 row = 1 response
- Contains: profile, AI usage, indexes, Likert block, qualitative feedback

Internal backend normalization:

- Main normalized fields: `employee_id`, `role`, `motivation`, `ai_usage`, `self_efficacy`, `talent_development`, `experience_years`, `acceptance`, `open_experience_ai_learning`, `open_challenges_ai_usage`, `open_training_needs`
- Legacy compatibility fields still required/produced by backend: `comment`, `last_goal` (they are backfilled from the open-text fields above to preserve compatibility with the legacy schema)
- `ai_usage` normalized to: `never`, `rarely`, `sometimes`, `frequently`, `always`

## 6) API / Endpoints

Base URL: `http://localhost:8000/api/v1`

**ES**

- `GET /dashboard/summary`
- `POST /surveys/upload` (multipart/form-data con `file`)
- `POST /chat/query`
- `POST /nlp/analyze`

**EN**

- `GET /dashboard/summary`
- `POST /surveys/upload` (multipart/form-data with `file`)
- `POST /chat/query`
- `POST /nlp/analyze`

### Example request / Ejemplo de petición (`POST /chat/query`)

```json
{
  "employee_role": "Technology",
  "learning_goal": "Python avanzado para ML",
  "ai_usage": "sometimes",
  "self_efficacy": 6.5,
  "motivation": 7.0
}
```

### Example response / Ejemplo de respuesta (`POST /surveys/upload`)

```json
{
  "rows_loaded": 1000,
  "message": "Survey dataset updated with 1000 rows"
}
```

## 7) Frontend / Cliente

**ES**

React (`frontend/`):

1. Dashboard con métricas, barras, correlaciones e insights.
2. Formulario de chatbot para recomendaciones.
3. Analizador NLP con entrada libre.
4. Carga de CSV para refrescar dataset.

**EN**

React (`frontend/`):

1. Dashboard with metrics, bars, correlations, and insights.
2. Chatbot form for recommendations.
3. NLP analyzer with free-text input.
4. CSV upload to refresh the dataset.

## 8) Google Forms Integration / Integración Google Forms

**ES**  
Script disponible en `scripts/create_evaluai_google_form.gs`.  
Crea formulario, vuelca respuestas en Sheets, genera `csv_ready` y exporta CSV en Drive.

**EN**  
Script available at `scripts/create_evaluai_google_form.gs`.  
It creates the form, writes responses to Sheets, maintains `csv_ready`, and exports CSV to Drive.

## 9) Repository Layout / Estructura

```text
backend/
  app/
    api/routes.py
    services/{analytics,recommender,nlp,data_store}.py
    models/schemas.py
    main.py
    config.py
  data/
    raw/survey_raw.xlsx
    courses.csv
    mentors.csv
  tests/test_api.py
frontend/
  src/App.jsx
  src/services/api.js
scripts/create_evaluai_google_form.gs
```

## 10) Local Run / Ejecución local

Recommended / Recomendado: **Python 3.11**.

1. Install dependencies / Instalar dependencias:

```bash
pip install -r backend/requirements.txt
```

2. Start API / Levantar API:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

## 11) Collaborators / Colaboradores

- Kirutasu Sánchez Serrano — @Kirutasu
- Ignacio Castillo Franco — @IgnacioCastilloFranco
- Bunty Nanwani Nanwani — @buntynanwani
- Alfonso Bermúdez Torres — @GHalfbbt

3. React (optional / opcional):

```bash
cd frontend
npm install
npm run dev
```

## 11) Docker

```bash
docker compose up --build
```

Services / Servicios:

1. Backend: `http://localhost:8000`
2. Frontend: `http://localhost:3000`

## 12) Tests

```bash
python -m pytest backend/tests/test_api.py
```

**ES**  
Cubre smoke tests de health, dashboard, chat y nlp.

**EN**  
Covers smoke tests for health, dashboard, chat, and nlp.

## 13) Environment Variables / Variables de entorno

- `EVALUAI_APP_NAME` (default: `EvaluAI API`)
- `EVALUAI_APP_DESCRIPTION` (default: `API to evaluate training impact with AI`)
- `EVALUAI_APP_VERSION` (default: `0.1.0`)
- `EVALUAI_API_PREFIX` (default: `/api/v1`)
- `EVALUAI_ALLOWED_ORIGINS` (default: `*`)
- `EVALUAI_SURVEYS_PATH` (default: `data/raw/survey_raw.xlsx`)
- `EVALUAI_COURSES_PATH` (default: `data/courses.csv`)
- `EVALUAI_MENTORS_PATH` (default: `data/mentors.csv`)
- `EVALUAI_CHAT_PROVIDER` (`rule_based` or `azure_foundry`, default: `rule_based`)
- `EVALUAI_AZURE_FOUNDRY_ENDPOINT` (Foundry model endpoint, e.g. `https://<resource>.services.ai.azure.com/models`)
- `EVALUAI_AZURE_FOUNDRY_API_KEY` (API key for inference endpoint)
- `EVALUAI_AZURE_FOUNDRY_MODEL` (deployed model name)
- `EVALUAI_AZURE_FOUNDRY_TEMPERATURE` (default: `0.2`)
- `VITE_API_BASE_URL` (React only, default: `http://localhost:8000/api/v1`)

## 14) Azure Foundry Chat Mode

The `/chat/query` endpoint supports two providers while keeping the same response schema used by the React UI:

1. `rule_based` (default): current deterministic recommender.
2. `azure_foundry`: uses Azure AI Foundry model inference and falls back to `rule_based` if inference/config fails.

Example:

```bash
EVALUAI_CHAT_PROVIDER=azure_foundry
EVALUAI_AZURE_FOUNDRY_ENDPOINT=https://<resource>.services.ai.azure.com/models
EVALUAI_AZURE_FOUNDRY_API_KEY=<your-key>
EVALUAI_AZURE_FOUNDRY_MODEL=gpt-4o-mini
```

## 15) MVP Limitations / Limitaciones

**ES**

1. Persistencia principal en memoria para encuestas subidas durante ejecución.
2. NLP basado en reglas/diccionarios.
3. Recomendador por overlap de tokens (sin embeddings).
4. Sin autenticación/autorización.
5. Sin versionado formal de datasets.

**EN**

1. Uploaded survey persistence is in-memory at runtime.
2. NLP is dictionary/rule-based.
3. Recommender uses token overlap (no embeddings).
4. No authentication/authorization.
5. No formal dataset versioning pipeline.
