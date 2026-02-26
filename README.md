# EvaluAI

MVP para evaluar el impacto de la formacion con IA en empleados, basado en el briefing del proyecto.

Incluye 3 modulos:

1. Dashboard de analitica (indicadores, distribucion de uso de IA, correlaciones, insights).
2. Chatbot de recomendacion (cursos, mentor, plan de 30 dias).
3. Analizador NLP de opiniones (sentimiento, temas y recomendaciones grupales).

## Stack

- Backend: FastAPI + Pandas
- Frontend web: React + Vite
- Cliente demo alternativo: Streamlit
- Datos: CSV

## Estructura relevante

- `backend/app/main.py`: app FastAPI.
- `backend/app/api/routes.py`: endpoints del MVP.
- `backend/app/services/`: logica de analytics, recomendaciones, NLP y repositorio.
- `backend/data/courses.csv`: catalogo de cursos.
- `backend/data/mentors.csv`: catalogo de mentores.
- `backend/data/datos_encuesta_formacion_ia.csv`: dataset principal de encuestas.
- `streamlit_app.py`: UI demo en Streamlit para los 3 modulos.
- `frontend/`: UI React.

## Endpoints

- `GET /api/v1/dashboard/summary`
- `POST /api/v1/surveys/upload` (multipart CSV)
- `POST /api/v1/chat/query`
- `POST /api/v1/nlp/analyze`

## Ejecucion local (Python)

Version recomendada: **Python 3.11** (alineada con `.devcontainer`).

1. Instala dependencias:

```bash
pip install -r requirements.txt
```

2. Levanta backend:

```bash
uvicorn backend.app.main:app --reload --host 0.0.0.0 --port 8000
```

3. (Opcional) Ejecuta Streamlit:

```bash
streamlit run streamlit_app.py
```

4. (Opcional) Ejecuta frontend React:

```bash
cd frontend
npm install
npm run dev
```

## Ejecucion con Docker

```bash
docker compose up --build
```

- Backend: `http://localhost:8000`
- Frontend: `http://localhost:3000`

## Variables de entorno

- `EVALUAI_ALLOWED_ORIGINS` (default: `*`)
- `EVALUAI_API_PREFIX` (default: `/api/v1`)
- `EVALUAI_SURVEYS_PATH` (default: `data/datos_encuesta_formacion_ia.csv`)
- `EVALUAI_COURSES_PATH` (default: `data/courses.csv`)
- `EVALUAI_MENTORS_PATH` (default: `data/mentors.csv`)
- `EVALUAI_API_BASE_URL` (solo Streamlit, default: `http://localhost:8000/api/v1`)
- `VITE_API_BASE_URL` (solo frontend React, default: `http://localhost:8000/api/v1`)
