# EvaluAI

## 1) Resumen unificado

EvaluAI es un proyecto para evaluar el impacto de la formación apoyada por IA. El objetivo es proporcionar insights accionables de datos de encuestas, recomendaciones personalizadas y un asistente conversacional. Esta versión consolida:

- `backend/app/*` (API, RAG, ML, supabase, seguridad)
- `frontend/src/*` (React/Vite, UI de dashboard/chat/NLP)
- `docs/*` (arquitectura, guías de implementaciones LLM, eval scripts)

## 2) ¿Qué hace?

- Dashboard de KPIs y correlaciones RRHH/L&D
- RAG + chatbot con LLM (Gemini + Azure Foundry)
- Analizador NLP para feedback cualitativo
- Subida y normalización de encuestas CSV
- Persistencia de sesiones, turns y recomendaciones en Supabase

## 3) Diseño de la arquitectura

### componentes

1. Frontend
   - `frontend/` (React + Vite) con rutas protegidas y permisos RRHH.
2. Backend
   - `backend/app/main.py`: FastAPI + CORS + startup seeds
   - Rutas: `chat_routes`, `kpi_routes`, `ml_routes`, `surveys_routes`, `campaign_routes`, `nlp_routes`
3. Chatbot
   - `backend/app/chatbot/`: gestión de contexto, RAG híbrido, prompt builder, parse response, PII guard

### flujo de chat

1. `/api/v1/chat/query` recibe request
2. Carga contexto empleado desde Supabase
3. `HybridRAGOrchestrator` propone cursos/mentores/programas
4. `ml_client` calcula scores de recomendación/riesgo
5. `PromptBuilder` arma prompt + `PIIGuard` anonimiza
6. LLM provider (`gemini` o `foundry`) consulta modelo
7. `response_parser` convierte a JSON y construye `ChatResponse`
8. Persiste `chat_sessions` + `chat_turns` + `recommendation_events`

## 4) Principales endpoints

- `GET /api/v1/health`
- `GET /api/v1/config`
- `POST /api/v1/chat/query`
- `GET /api/v1/chat/history?user_id=<>&limit=10`
- `GET /api/v1/kpi/summary` (y demás KPI)
- `POST /api/v1/upload/surveys` (o `POST /api/v1/surveys/upload`) CSV
- `GET /api/nlp/summary`
- `GET /api/nlp/executive`
- `GET /api/nlp/employee/{employee_id}`

### Ejemplo chat request

```json
{
  "user_id": "U123",
  "message": "Busco mejorar mis habilidades en IA aplicada a finanzas",
  "provider": "gemini",
  "employee_context": { "department": "Finanzas", "ai_usage_frequency": 3 }
}
```

## 5) Data model y persistencia

- `DataManager` (Supabase): empleados, encuestas, cursos, mentores, sesiones chat
- `chat_sessions` (goal_detected, goal_clarity, depth)
- `chat_turns` (rol, mensaje, timestamp)
- `recommendation_events` (curso, mentor, plan)
- `backend/data/raw` (survey_raw.xlsx, cursos, mentores, eval cases, logs JSONL)

## 6) Configuración y variables importantes

### .env principales
- `SUPABASE_URL`, `SUPABASE_KEY`
- `GEMINI_API_KEY`
- `EVALUAI_AZURE_FOUNDRY_ENDPOINT`, `EVALUAI_AZURE_FOUNDRY_API_KEY`, `EVALUAI_AZURE_FOUNDRY_MODEL`
- `CHATBOT_GEMINI_MODEL`, `CHATBOT_GEMINI_MAX_RETRIES`, `TABOT_CONVERSATION_MAX_TURNS`

### AppConfig relevantes
- `EVALUAI_API_PREFIX` (/api/v1)
- `EVALUAI_ALLOWED_ORIGINS` (*)
- `EVALUAI_SURVEYS_PATH`, `EVALUAI_COURSES_PATH`, `EVALUAI_MENTORS_PATH`
- `PII_GUARD_ENABLED` para evitar salir datos sensibles

## 7) Cómo ejecutar

### Backend
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Docker (opcional)
```bash
docker compose up --build
```

## 8) Testing

```bash
cd backend
pytest -q
```

## 9) Archivos de documentación clave

- `docs/chatbot_technical_design.md`
- `docs/llm_implementations_guide.md`
- `docs/foundry_eval_runs.md`
- `scripts/run_chat_eval.py`

## 10) Notas de estado actual

- `backend/app/api/routes.py` está deprecado; uso actual en rutas específicas.
- `backend/app/chatbot` usa `GeminiChatClient` y `FoundryChatClient`.
- `backend/app/config.py` valida env vars y define valores por defecto.
- La frontend guarda login y roles en `AuthContext`.

---

### Colaboradores
- Kirutasu Sánchez Serrano — @Kirutasu
- Ignacio Castillo Franco — @IgnacioCastilloFranco
- Bunty Nanwani Nanwani — @buntynanwani
- Alfonso Bermúdez Torres — @GHalfbbt

