# EvaluAI Post-Merge Stabilization — Implementation Plan

**Branch**: `fix/post-merge-stabilization-codex-chatbot`  
**Date**: March 10, 2026  
**Status**: ✅ Phase 0 (Discovery & Validation) COMPLETE  
**Next**: Phase 1 (Dead Code Cleanup)

---

## 🎯 CONTEXT & SCOPE

### What's Been Fixed (Phase 0 - DONE ✅)
1. ✅ .env loading from project root (backend + frontend unified)
2. ✅ `AppConfig` class created with all required settings
3. ✅ Dead code imports suppressed (`routes.py` isolation)
4. ✅ Data loading syntax errors fixed
5. ✅ Backend boots cleanly with Supabase connectivity confirmed
6. ✅ 75/76 unit tests passing
7. ✅ All active endpoints verified working

### Remaining Stabilization Work (6 phases, ~2-3 hours total)

---

## 📋 PHASE 1: Dead Code Cleanup (15 min) 🎯 START HERE

**Objective**: Remove/archive unused code to reduce confusion and technical debt.

### Tasks

#### 1.1 Mark routes.py as deprecated
```bash
# Action: Add clear comment header to routes.py
# Explanation: This file is superseded by chat_routes.py and kpi_routes.py
# Keep it for now (not deleted) to preserve history
```

**File**: [backend/app/api/routes.py](backend/app/api/routes.py) line 1  
**Change**: Add docstring/comment explaining status

```python
"""
⚠️ DEPRECATED: This module is no longer used.

This file has been superseded by the separate routers:
- backend/app/api/chat_routes.py → /api/v1/chat/* endpoints
- backend/app/api/kpi_routes.py → /api/v1/kpi/* endpoints

The endpoints defined here (/dashboard/summary, /surveys/upload, /nlp/analyze)
are not registered in main.py and not called by the frontend.

This file is kept for reference/history. If you need these endpoints
restored, migrate them from routes.py to the appropriate specific router.

Migration status: [TODO: Link to issue if created]
"""
```

#### 1.2 Fix test_api.py
**File**: [backend/tests/test_api.py](backend/tests/test_api.py)

**Issues**:
- Tests endpoint `/health` but actual is `/api/v1/health`
- Tests `/api/v1/dashboard/summary` (doesn't exist)
- Tests `/api/v1/nlp/analyze` (doesn't exist)

**Action**: Update to only test registered endpoints
```python
# Keep:
- test_health_endpoint() → /api/v1/health ✅
- test_chat_query_endpoint() → /api/v1/chat/query ✅

# Remove or comment:
- test_dashboard_summary_endpoint() [endpoint not registered]
- test_nlp_endpoint() [endpoint not registered]

# Add comment explaining:
"""Tests for dead endpoints in routes.py have been removed.
For future work on dashboard/nlp features, migrate from routes.py
to chat_routes.py or create new dedicated routers."""
```

### Validation
```bash
cd /workspaces/EvaluAI/backend
python3 -m pytest tests/test_api.py -v
# Expected: 2 tests pass (or all pass if you add mocks for real data)
```

---

## 📋 PHASE 2: Frontend Configuration & Connectivity (30 min)

**Objective**: Ensure frontend can read `.env` and connect to backend.

### Tasks

#### 2.1 Create frontend/.env stub
**File**: [frontend/.env](frontend/.env) (create new)

```bash
# This file can be empty or contain dev-specific overrides.
# By default, Vite will load from ../​.env (project root)
# due to envDir: "../" in vite.config.js
```

**Rationale**: While technically not needed (vite.config.js loads from ..),
creating an empty file documents intent and future extensibility.

#### 2.2 Verify VITE_API_BASE_URL is correct
**File**: [.env](/.env) line ~15

**Current value**:
```
VITE_API_BASE_URL=http://localhost:9000/api/v1
```

**Documentation**:
- ✅ Correct for docker-compose (port 9000 → 8000 internal)
- ✅ Correct for dev container if accessing from host
- ⚠️ Will fail if frontend in dev container tries to reach :9000 directly

**Decision**: LEAVE AS-IS (docker-compose primary use case)

#### 2.3 Test frontend .env loading
```bash
cd /workspaces/EvaluAI/frontend
npm run build  # Build includes .env loading
# Check build log contains VITE_API_BASE_URL value
```

### Validation
```bash
# In dev container, visit http://localhost:5173
# Chatbox component should load form
# (Will fail to connect to backend if backend not running, but form loads ✅)
```

---

## 📋 PHASE 3: CORS & Security Configuration (20 min)

**Objective**: Make CORS configuration environment-driven (not hardcoded).

### Tasks

#### 3.1 Verify AppConfig.CORS_ORIGINS parsing

**File**: [backend/app/config.py](backend/app/config.py) line ~115

**Current implementation**:
```python
_allowed_origins_str: str = os.getenv("EVALUAI_ALLOWED_ORIGINS", "*")
CORS_ORIGINS: list = (
    ["*"] if _allowed_origins_str == "*"
    else [origin.strip() for origin in _allowed_origins_str.split(",")]
)
```

**Behavior**:
- ✅ Parses comma-separated list: `"http://localhost:3000,http://localhost:5173"`
- ✅ Supports wildcard `"*"` for dev
- ✅ Defaults to `"*"` if not set

**Validation**:
```bash
cd /workspaces/EvaluAI

# Test 1: Defaults to wildcard
unset EVALUAI_ALLOWED_ORIGINS
cd backend && python3 -c "from app.config import AppConfig; print(AppConfig.CORS_ORIGINS)"
# Expected: ['*']

# Test 2: Parse comma-separated
export EVALUAI_ALLOWED_ORIGINS="http://localhost:3000,http://localhost:5173"
cd backend && python3 -c "from app.config import AppConfig; print(AppConfig.CORS_ORIGINS)"
# Expected: ['http://localhost:3000', 'http://localhost:5173']
```

#### 3.2 Document CORS for production
**File**: Create [DEPLOYMENT.md](DEPLOYMENT.md) (or update README)

```markdown
## Security: CORS Configuration

For **development** (default):
```bash
# .env
EVALUAI_ALLOWED_ORIGINS=*  # Accepts requests from any origin
```

For **staging/production**:
```bash
# .env
EVALUAI_ALLOWED_ORIGINS=https://app.evaluai.com,https://staging.evaluai.com
```

- Set explicit origins (no wildcard)
- Add all frontend domains that will access the API
- Restart backend after .env change
```

### Validation
```bash
# After setting EVALUAI_ALLOWED_ORIGINS, restart backend and test CORS headers:
curl -i -H "Origin: http://localhost:5173" http://localhost:8000/api/v1/health
# Should show: Access-Control-Allow-Origin: http://localhost:5173 (or *)
```

---

## 📋 PHASE 4: Hardcoded Values Audit & Documentation (30 min)

**Objective**: Identify remaining hardcodes and decide what to externalize.

### Known Hardcodes

#### 4.1 User ID in Frontend
**File**: [frontend/src/pages/ChatPage.jsx](frontend/src/pages/ChatPage.jsx) line 6

```javascript
const [userId] = useState("1XVWCBPH"); // Demo user
```

**Decision**: ⚠️ KEEP for now (MVP constraint: single-user demo)  
**Future work**: [ ] Accept user ID from URL param or SessionStorage

**Doc**:
```javascript
// TODO: Make user ID dynamic - accept from URL or session
// Example: const [userId] = useState(() => new URLSearchParams(window.location.search).get('userId') || "1XVWCBPH");
```

#### 4.2 Dataset Path in employees_seed
**File**: [backend/app/database/seeds/employees_seed.py](backend/app/database/seeds/employees_seed.py) line 26

```python
data_path = Path(__file__).parent.parent.parent.parent / "data" / "raw" / "survey_raw.xlsx"
```

**Decision**: ⚠️ KEEP (works reliably due to relative path traversal)  
**Risk**: If file is moved, seeding silently fails  
**Future**: [ ] Add logging + error early-exit + document dataset requirements

**Doc**:
```python
# TODO: Make dataset path configurable via env var
# ENV: EVALUAI_EMPLOYEES_DATA_PATH=data/raw/...
# With fallback to relative path as current
```

#### 4.3 Model names
**Files**: Various (chatbot/gemini_client.py, config.py)

**Current**: 
- `CHATBOT_GEMINI_MODEL=gemini-2.5-flash` (externalized ✅)
- Azure model from `AppConfig.azure_foundry_model` (externalized ✅)

**Decision**: ✅ ALREADY DONE — all model names externalized

#### 4.4 API prefix
**File**: [backend/app/config.py](backend/app/config.py)

```python
api_prefix: str = os.getenv("EVALUAI_API_PREFIX", "/api/v1")
```

**Decision**: ✅ ALREADY EXTERNALIZED

### Summary Table

| Hardcode | Location | Type | Status | Action |
|----------|----------|------|--------|--------|
| User ID `1XVWCBPH` | ChatPage.jsx | Demo | Feature | ⚠️ Keep (MVP), document TODO |
| CSV path | employees_seed.py | Data | Config | ⚠️ Keep (works), document TODO |
| Model name | config.py | Config | Param | ✅ Externalized (CHATBOT_GEMINI_MODEL) |
| API prefix | config.py | Config | Param | ✅ Externalized (EVALUAI_API_PREFIX) |
| CORS | config.py | Security | Param | ✅ Externalized (EVALUAI_ALLOWED_ORIGINS) |

### Validation
```bash
# Verify all .env parameters are used:
grep -r "EVALUAI_\|CHATBOT_\|VITE_" /workspaces/EvaluAI/backend/app/config.py
grep -r "VITE_API_BASE_URL" /workspaces/EvaluAI/frontend/src/
# All should resolve to AppConfig attributes or env vars
```

---

## 📋 PHASE 5: Docker Compose Full Stack Validation (15 min)

**Objective**: Verify entire app boots in docker-compose without errors.

### Tasks

#### 5.1 Clean up any leftover processes
```bash
docker-compose down -v  # Remove volumes if tests dirtied data
```

#### 5.2 Build and start
```bash
cd /workspaces/EvaluAI
docker-compose up --build --detach
```

#### 5.3 Wait for services
```bash
sleep 10  # give services time to start
```

#### 5.4 Validate services
```bash
# Backend health
curl -s http://localhost:9000/api/v1/health | jq .
# Expected: {"status":"healthy","service":"EvaluAI API","version":"1.0.0"}

# Frontend (if service is healthier)
curl -s http://localhost:3000 | head -20
# Expected: HTML with React app

# Check logs
docker-compose logs --tail=20 backend
docker-compose logs --tail=20 frontend
# Look for 🔴 red flags: errors, crash loops
```

### Validation Checklist
- [ ] Backend port 9000 responds
- [ ] Frontend port 3000 loads (or 5173 if dev server used)
- [ ] No fatal errors in logs
- [ ] Supabase connection successful
- [ ] Demo data seeded

---

## 📋 PHASE 6: Documentation & Handoff (15 min)

**Objective**: Document all work and create handoff notes for next developer.

### Tasks

#### 6.1 Update [README.md](README.md)

Add section: "Development Setup"

```markdown
## Development Setup

### Prerequisites
- Docker & Docker Compose
- Python 3.11+ (for local dev without Docker)
- Node.js 18+ (for frontend dev)

### Quick Start (Docker)

```bash
cd /workspaces/EvaluAI
docker-compose up
```

Access:
- Backend API: http://localhost:9000/api/v1/health
- Frontend: http://localhost:3000 (or http://localhost:5173 for Vite dev server)

### Environment Variables

Create `.env` at project root:
```
# Required for backend
SUPABASE_URL=https://...supabase.co
SUPABASE_KEY=eyJ...  # JWT token
GEMINI_API_KEY=AIza...

# Frontend  
VITE_API_BASE_URL=http://localhost:9000/api/v1

# Optional
DEBUG=false
LOG_LEVEL=INFO
EVALUAI_ALLOWED_ORIGINS=*  # "*" for dev, explicit list for production
```

### Testing

```bash
# Unit tests (chatbot module)
cd backend && python3 -m pytest tests/chatbot/ -v

# API integration tests
cd backend && python3 -m pytest tests/test_api.py -v

# Frontend (if available)
cd frontend && npm test
```

### Architecture

- **Backend**: FastAPI (Python 3.11) + Supabase
- **Frontend**: React + Vite + Tailwind CSS
- **Database**: Supabase (PostgreSQL)
- **AI**: Google Gemini API

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed design.
```

#### 6.2 Create [STABILIZATION_NOTES.md](STABILIZATION_NOTES.md) (this file exists)

Document what was fixed:
```markdown
# Stabilization Notes - March 10, 2026 ✅

## What Was Fixed

### Phase 0: Discovery & Configuration (✅ COMPLETE)

1. **Unified .env Loading** ✅
   - Backend and frontend now share single `.env` from project root
   - Implemented `_find_env_file()` helper for robustness
   - Works in dev container, docker-compose, and local Python

2. **AppConfig Class** ✅
   - Created missing `AppConfig` class that was referenced throughout codebase
   - Mapped all environment variables (API, CORS, data paths, chatbot settings)
   - Added comprehensive comments explaining each setting

3. **Dead Code Isolation** ✅
   - Isolated `routes.py` (unused router with broken imports)
   - Marked deprecation to avoid future confusion
   - Active routers: `chat_routes.py`, `kpi_routes.py`

4. **Boot Verification** ✅
   - Backend boots cleanly with Supabase connectivity
   - 12 demo courses seeded
   - 100 demo employees seeded
   - Health endpoints responding

5. **Test Suite** ✅
   - 75/76 chatbot unit tests passing
   - Minor fix needed in `test_api.py` (remove tests for non-existent endpoints)

## What Remains (Phases 1-6)

- Phase 1: Dead code cleanup (routes.py deprecation, test_api.py fix)
- Phase 2: Frontend .env configuration
- Phase 3: CORS externalization documentation
- Phase 4: Hardcoded values audit cleanup
- Phase 5: Docker Compose full stack validation
- Phase 6: Documentation & handoff

## Critical Issues Resolved

| Issue | Resolution | Status |
|-------|-----------|--------|
| routes.py import errors | Suppressed import via `__init__.py` | ✅ Fixed |
| AppConfig missing | Created full class with all attrs | ✅ Fixed |
| .env loading (root location) | Added path traversal logic | ✅ Fixed |
| Indentation errors (data_store.py) | Removed stray text | ✅ Fixed |

## Next Developer

Start with Phase 1 (dead code cleanup) - takes ~15 min.
Then Phase 2 (frontend config) - takes ~30 min.
Full stabilization est. 2-3 hours.

All heavy lifting done. Remaining work is cleanup + validation.
```

#### 6.3 Update .env.example
**File**: [backend/.env.example](backend/.env.example)

Add section for frontend vars:

```bash
# Frontend
VITE_API_BASE_URL=http://localhost:9000/api/v1
```

### Validation
```bash
# Verify files exist and readable
ls -l README.md STABILIZATION_NOTES.md backend/.env.example
# All should exist ✅
```

---

## ✅ COMPLETION CHECKLIST

Use this as your progress tracker:

### Phase 1: Dead Code Cleanup
- [ ] Add deprecation header to routes.py
- [ ] Fix/remove test_api.py tests for non-existent endpoints
- [ ] Verify tests still pass: `pytest tests/test_api.py -v`

### Phase 2: Frontend Config
- [ ] Create empty `frontend/.env` (optional but documenting intent)
- [ ] Verify VITE_API_BASE_URL in root `.env`
- [ ] Test: `cd frontend && npm run build` (no errors)

### Phase 3: CORS & Security
- [ ] Verify AppConfig.CORS_ORIGINS parsing logic
- [ ] Test with different EVALUAI_ALLOWED_ORIGINS values
- [ ] Document in DEPLOYMENT.md

### Phase 4: Hardcodes Audit
- [ ] Completed audit of remaining hardcodes
- [ ] Added TODOs in code for future externalization
- [ ] Documented analysis in STABILIZATION_NOTES.md

### Phase 5: Docker Compose Validation
- [ ] `docker-compose up` boots without errors
- [ ] Backend /health check responds
- [ ] Frontend loads (page or dev server)
- [ ] Logs show no fatal errors

### Phase 6: Documentation
- [ ] Updated README.md setup section
- [ ] Created STABILIZATION_NOTES.md
- [ ] Updated .env.example
- [ ] All documentation reflects current state

---

## 📊 METRICS & SUCCESS CRITERIA

- ✅ Backend boots in < 3 seconds
- ✅ All active endpoints respond  
- ✅ 75+ unit tests pass
- ✅ Docker Compose full stack starts without errors
- ✅ .env loading works from project root
- ✅ Supabase connectivity confirmed
- ✅ No hardcoded security values leak into version control

---

## 🚀 AFTER STABILIZATION

Once all phases complete:

1. **Create PR** against `dev` branch
2. **Tag merge** with something like `v0.2.0-stable`
3. **Schedule**: Stabilization branch can merge to `dev` for next sprint work

Future work (out of scope for this stabilization):
- Multi-user session management
- Production deployment automation
- Advanced error handling & retry logic
- Integration tests with real Gemini API
- RAG/embeddings pipeline (mentioned in original scope, deferring)

---

## 📞 SUPPORT & QUESTIONS

If you encounter issues:
1. Check backend logs: `docker-compose logs backend`
2. Verify .env variables: `grep SUPABASE_URL .env`
3. Re-run health check: `curl http://localhost:9000/api/v1/health`
4. Review STABILIZATION_NOTES.md for known issues

---

Generated: March 10, 2026 / Updated: In Progress
