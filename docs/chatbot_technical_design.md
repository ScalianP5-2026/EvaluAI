# Chatbot Technical Design

Last updated: 2026-03-19

## 1. Purpose

This document explains the current technical design of the EvaluAI chatbot:

- architecture and module structure
- end-to-end request flow
- data and retrieval strategy (Hybrid RAG)
- LLM integration (Gemini and Azure Foundry)
- design decisions and tradeoffs
- known limitations and next steps

It reflects the implementation currently in this repository.

## 2. Scope and Goals

Primary goal: provide personalized training advice (courses, mentors, 30-day plans, insights) using employee context plus catalog knowledge.

Core requirements implemented:

- personalized responses based on employee profile and assessments
- support for different LLM providers behind one interface
- hybrid retrieval from structured DB plus file knowledge
- JSON response contract for predictable API behavior
- conversation history persistence
- recommendation traceability and basic retrieval metrics

## 3. High-Level Architecture

```text
Frontend (React ChatPage/ChatBox)
    |
    | POST /api/v1/chat/query
    v
FastAPI chat route (chat_routes.py)
    |
    +--> DataManager (Supabase: employee + catalog + stats)
    |
    +--> HybridRAGOrchestrator
    |       - structured retrieval (Supabase courses/mentors)
    |       - file retrieval (CSV catalogs/profiles)
    |       - ranking + explainable reasons
    |
    +--> ML client (recommendation/risk scores)
    |
    +--> PromptBuilder (strict JSON prompt contract)
    |
    +--> LLM Client
    |       - GeminiChatClient OR FoundryChatClient
    |
    +--> Response Parser (JSON extraction + fallback)
    |
    +--> Supabase persistence (sessions, turns, recommendation events)
    |
    +--> local JSONL metrics (hybrid_rag_events.jsonl)
```

## 4. Module Structure

### Backend chatbot modules

- `backend/app/chatbot/settings.py`
  - central env-driven config (provider, model, retries, timeouts, memory limits)
- `backend/app/chatbot/foundry_client.py`
  - Azure OpenAI/Foundry chat client with endpoint normalization
- `backend/app/chatbot/gemini_client.py`
  - Gemini async wrapper with retries and timeout
- `backend/app/chatbot/data_manager.py`
  - Supabase data access and query-scoped employee fact retrieval
- `backend/app/chatbot/hybrid_rag.py`
  - hybrid retrieval and ranking for courses and mentors
- `backend/app/chatbot/prompt_builder.py`
  - prompt assembly with strict JSON output contract
- `backend/app/chatbot/response_parser.py`
  - robust parse strategy (direct JSON, extraction, fallback)
- `backend/app/chatbot/conversation.py`
  - in-memory turn tracking and metadata heuristics
- `backend/app/chatbot/rag_metrics.py`
  - writes retrieval/ranking snapshots to JSONL

### API layer

- `backend/app/api/chat_routes.py`
  - `/api/v1/chat/query`
  - `/api/v1/chat/history`
  - orchestrates all chatbot components

### Frontend integration

- `frontend/src/pages/ChatPage.jsx`
  - loads chat history and sends messages
- `frontend/src/components/Chatbox.jsx`
  - chat UI and message list
- `frontend/src/services/api.js`
  - `chatAPI.sendMessage`, `chatAPI.getHistory`

## 5. End-to-End Request Flow

Endpoint: `POST /api/v1/chat/query`

1. Create `session_id` for the turn.
2. Load canonical employee context from Supabase using `DataManager.get_employee_context`.
3. If request has `employee_context`, merge as override, but keep canonical full profile source.
4. Build query-scoped employee facts with `get_retrieved_facts_for_query`.
   - Important decision: do not send full profile to LLM; only scoped facts.
5. Build baseline RAG context:
   - similar profiles summary
   - department insights
6. Run `HybridRAGOrchestrator`:
   - gather course and mentor candidates from DB and CSV files
   - rank candidates
   - produce citations, tool trace, and evaluation snapshot
7. Attach ML scores from `ml_client.get_employee_scores`.
8. Load recent history from last chat session and hydrate `ConversationMemory`.
9. Build prompt with `PromptBuilder.build_contextual_prompt`.
10. Query active provider (`GeminiChatClient` or `FoundryChatClient`).
11. Parse model output through `parse_response`.
12. Build typed `ChatResponse`.
13. Persist to Supabase:
    - `chat_sessions`
    - `chat_turns` (user + assistant)
    - `recommendation_events` (if recommendation exists)
14. Persist hybrid retrieval snapshot to:
    - `backend/data/processed/hybrid_rag_events.jsonl`
15. Return response to frontend.

Endpoint: `GET /api/v1/chat/history`

- loads latest session by employee id
- returns last `limit` turns in chronological order
- normalizes older assistant JSON blobs to plain message text

## 6. Data and Context Design

### 6.1 Employee context model

`DataManager.get_employee_context` composes:

- employee core row (`employees`)
- latest assessment (`employee_assessments`)
- latest survey answer (`survey_answers`)
- recommendation history (`recommendation_events`)

Compact fields used in prompt:

- department
- education level
- motivation
- self-efficacy
- AI usage frequency
- age
- years in company
- retrieved_facts (query-scoped subset)

### 6.2 Structured retrieval (query-scoped)

`get_retrieved_facts_for_query` classifies user query intent into scopes:

- core_profile
- tenure
- identity
- ai_usage
- assessments
- recommendations

It then returns only relevant facts and counters instead of raw full-table payloads.

### 6.3 Hybrid RAG sources

Structured sources (Supabase):

- `courses`
- `mentores`

File sources:

- `backend/data/raw/programas_formacion.csv`
- `backend/data/raw/mentores.csv`
- `backend/data/mentors.csv` (human-readable mentor profiles + email)

### 6.4 Hybrid ranking

Course ranking factors:

- goal similarity
- skill similarity
- department fit
- level fit
- historical performance signal
- novelty vs prior recommendations

Mentor ranking factors:

- skill similarity
- query similarity
- availability fit
- competence signal
- department fit

The orchestrator returns:

- ranked courses
- ranked mentors
- recommended programs
- score breakdown and reasons
- citations
- evaluation snapshot
- tool trace

## 7. Prompt and Response Contract

### 7.1 Prompt strategy

PromptBuilder injects:

- employee profile summary
- retrieved employee facts
- ML scores
- RAG context (courses, mentors, programs)
- mentor contacts (emails)
- hybrid citations/evaluation trace
- recent conversation turns

### 7.2 Output contract

The model is instructed to return JSON only with:

- `message`
- `recommendations` (`course`, `mentor`, `plan_30_days`)
- `insights` (`general`, `department`, `personal`)
- `metadata` (`goal_detected`, `goal_clarity`, `recommended_skill`)
- `risk_alert`

### 7.3 Parsing safeguards

`response_parser.py` pipeline:

1. direct JSON parse
2. extract JSON object from text and parse again
3. fallback payload when parsing fails

This prevents total request failure on model formatting errors.

## 8. LLM Provider Abstraction

Provider selection is environment-driven:

- `CHATBOT_LLM_PROVIDER=gemini`
- `CHATBOT_LLM_PROVIDER=foundry` (or `azure_foundry`, `azure_openai`)

### Gemini path

- `GeminiChatClient`
- configured via `CHATBOT_GEMINI_*` variables

### Foundry path

- `FoundryChatClient`
- configured via `CHATBOT_FOUNDRY_*` variables
- endpoint normalization accepts:
  - full chat completions URL
  - deployment root URL
  - resource base URL + deployment name

## 9. Persistence and Observability

### Supabase persistence

- `chat_sessions`: session-level metadata
- `chat_turns`: user and assistant messages
- `recommendation_events`: recommendation logging for downstream analytics

### Local retrieval metrics

- `backend/data/processed/hybrid_rag_events.jsonl`
- one event per query with retrieval and ranking diagnostics

This enables offline review of ranking quality and recommendation drift.

## 10. Frontend Integration Details

### Send flow

- `ChatPage` sends `user_id`, `message`, optional `employee_context` via `chatAPI.sendMessage`.
- UI appends optimistic user turn and final assistant `response.message`.

### History flow

- `chatAPI.getHistory` fetches backend history.
- assistant content is normalized to avoid rendering raw JSON blobs.

### Auth linkage

- user identity comes from auth context (`employee_id`).
- token is attached by Axios interceptor.

## 11. Key Design Decisions and Why

1. Hybrid retrieval instead of prompt-only generation.
   - Improves grounding and makes recommendations traceable.

2. Query-scoped employee facts instead of full profile prompt injection.
   - Reduces token usage and privacy exposure while preserving factual answers.

3. Strict JSON response contract.
   - Keeps backend behavior predictable and frontend rendering simple.

4. Provider abstraction (Gemini and Foundry).
   - Allows cloud/provider migration without changing business orchestration.

5. Explainable ranking with score breakdown and reasons.
   - Supports debugging and future trust/quality evaluation.

6. Retrieval event logging to JSONL.
   - Lightweight analytics without adding immediate DB schema complexity.

7. Merge of structured DB data plus local file catalogs.
   - Handles incomplete catalogs while preserving quick iteration.

## 12. Known Limitations

1. Chat routes are not currently protected by auth dependency in backend.
   - Frontend sends JWT, but route does not enforce token-to-user validation.

2. Session model creates a new `session_id` per query.
   - History continuity is reconstructed from latest stored turns, not long-lived in-memory sessions.

3. `TrainingSessionTracker` is instantiated but not persisted/used meaningfully yet.

4. Ranking is lexical/token based (Jaccard), not embedding/vector retrieval yet.

5. Local JSONL metrics can be ephemeral in containerized deployments unless volume-mounted.

6. Several legacy comments and docs still mention old Gemini-only flow.

## 13. Suggested Evolution

1. Enforce auth on chat routes and validate `user_id` against JWT `sub`.
2. Introduce stable conversation session IDs across multiple turns.
3. Move retrieval metrics to Supabase table for durable analytics.
4. Add embedding-based retrieval and hybrid reranking.
5. Add guardrails/tests for prompt and parser schema drift.
6. Add explicit source attribution in API response for transparency.
7. Consolidate and modernize docs (`backend/app/chatbot/README.md`) with this design.

## 14. Configuration Summary

Main env groups:

- provider switch: `CHATBOT_LLM_PROVIDER`
- Gemini: `CHATBOT_GEMINI_*`
- Foundry: `CHATBOT_FOUNDRY_*`
- conversation memory: `CHATBOT_CONVERSATION_*`
- goal detection keywords: `CHATBOT_GOAL_DETECTION_KEYWORDS`
- logging/debug: `CHATBOT_LOG_LEVEL`, `CHATBOT_DEBUG_MODE`

For local startup, backend also seeds required data on app startup:

- courses
- mentors
- employees
- user credentials

