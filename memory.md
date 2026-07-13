# Project Memory

> Auto-maintained by coding agents. Do not delete.

## Project Overview
- **Name:** SkillTree AI
- **Purpose:** Gamified developer learning platform with skill trees, quests, XP, leaderboards, and AI-assisted code evaluation
- **Stack:** React 19 + Vite (frontend), Django 6 + DRF + Celery + Redis (backend), SQLite (dev DB), MongoDB (migration target), ChromaDB (vector store), LM Studio (local AI inference)
- **Entry Point:** `frontend/src/main.jsx` (UI), `backend/manage.py` (API), `run_dev.ps1` (launcher)

## Architecture
```
skilltree-ai/
├── frontend/          # React 19 + Vite + Tailwind + Framer Motion + Three.js/R3F + React Flow
├── backend/
│   ├── core/          # Django settings, URLs, Celery config
│   ├── users/         # Custom User model with XP/profile
│   ├── auth_app/      # JWT auth endpoints
│   ├── skills/        # Skill tree logic
│   ├── quests/        # Quest system
│   ├── leaderboard/   # Leaderboard
│   ├── ai_evaluation/ # AI-assisted code grading
│   ├── executor/      # Sandboxed code execution
│   ├── mentor/        # AI mentor
│   ├── multiplayer/   # Multiplayer features
│   ├── mongo/         # MongoDB migration layer
│   └── mail-server.js # Node.js contact mail microservice
├── docs/              # Architecture and DB docs
├── scripts/           # Project utilities
└── run_dev.ps1        # Dev environment launcher
```

## Key Decisions
- `backend/.env` must contain `SECRET_KEY`, `DEBUG=True`, and `ALLOWED_HOSTS` for local dev — these are separate from the root `.env`
- `settings.py` will raise `ImproperlyConfigured` if `SECRET_KEY` is missing and `DEBUG` is not `True`
- Dev database defaults to SQLite (`db.sqlite3`); PostgreSQL is for production
- MongoDB migration is underway; `USE_MONGODB=True` enables MongoEngine bootstrapping

## Dependencies
- Django 6, DRF, SimpleJWT, dj-database-url, python-dotenv, Celery, Redis, ChromaDB, MongoEngine
- React 19, Vite, Tailwind CSS, Framer Motion, Three.js/R3F, React Flow, lucide-react, Zustand

## Environment
Required env vars in `backend/.env`:
- `SECRET_KEY` — Django secret key
- `DEBUG=True` — enables dev mode and fallback key logic
- `ALLOWED_HOSTS` — comma-separated list
- `DATABASE_URL` — defaults to `sqlite:///db.sqlite3`
- `REDIS_URL` — defaults to `redis://localhost:6379/0`
- `LM_STUDIO_URL`, `LM_STUDIO_MODEL` — local AI inference
- `MONGODB_URI`, `MONGODB_DB`, `USE_MONGODB` — MongoDB config
- Gmail vars for mail microservice

## Change Log

### 2026-07-07 10:04 — Fix: Django backend fails to start (ERR_CONNECTION_REFUSED)
- **Changes Made:**
  - Added missing `SECRET_KEY`, `DEBUG=True`, `ALLOWED_HOSTS`, `DATABASE_URL`, `REDIS_URL`, `JWT_*`, `CHROMA_PATH` to `backend/.env`
- **SOLID Principles Applied:** N/A (config fix)
- **Files Modified:** `backend/.env`
- **Bugs Fixed:** Django raised `ImproperlyConfigured: SECRET_KEY environment variable is required in production mode` because `backend/.env` had only mail/MongoDB vars but was missing core Django settings. Root `.env` is NOT loaded by Django since `load_dotenv()` runs from the `backend/` directory.
- **Breaking Changes:** No
- **Next Agent Notes:** `backend/.env` and root `.env` are separate files. Always ensure `backend/.env` contains the Django core vars. The `SECRET_KEY` here is a dev placeholder — replace for production.

### 2026-07-07 10:20 — Fix: ASGI worker killed on POST /api/skills/generate/
- **Changes Made:**
  - `AutoFillQuestsView.post()` was calling `QuestAutoFillService().execute_autofill()` synchronously inside the ASGI request handler. This triggered blocking `requests.post()` calls to LM Studio for every stub quest (potentially 20+ calls × 30s timeout each), starving the Daphne ASGI event loop until it killed the connection.
  - Fixed by dispatching `autofill_quests_task.delay(str(tree_id))` (Celery) instead — matching the established pattern in `GenerateSkillTreeView`.
- **SOLID Principles Applied:** SRP — view layer should not perform heavy I/O; that belongs in the task/service layer.
- **Files Modified:** `backend/skills/views.py`
- **Bugs Fixed:** "Application instance for connection POST /api/skills/generate/ took too long to shut down and was killed" — root cause: synchronous blocking LM Studio HTTP in ASGI view.
- **Breaking Changes:** No. Response shape changes from `{status, tree_id, quests_filled, ...}` to `{status: 'generating', tree_id, message}` (202 Accepted), consistent with the tree generation endpoint.
- **Next Agent Notes:** Both `GenerateSkillTreeView` and `AutoFillQuestsView` now correctly return immediately with 202 and let Celery do the heavy lifting. Progress is broadcast via WebSocket (`ws/skills/autofill/{tree_id}/`).

### 2026-07-07 10:23 — Fix: Two LM Studio / Celery bugs from Gemma 4 26B usage

#### Bug 1 — `response_format: {"type": "json_object"}` rejected (HTTP 400)
- **Root Cause:** `weekly_report.py._generate_narrative()` passed `response_format={"type": "json_object"}` to `lm_client.chat_completion()`. Gemma 4 (and most local LM Studio models) only accept `type='json_schema'` or `type='text'`; `json_object` is an OpenAI-specific extension not supported here.
- **Fix:** Removed `response_format` argument entirely. The system prompt already instructs the model to respond with JSON-only, which is sufficient.
- **Files Modified:** `backend/users/weekly_report.py`

#### Bug 2 — `RemoteDisconnected` during tree generation (LM Studio drops connection)
- **Root Cause:** Large model (Gemma 4 26B, ~18GB) takes >60s to generate a full skill tree (3000 max_tokens). LM Studio drops idle keep-alive TCP connections mid-inference, causing `urllib3` to raise `RemoteDisconnected`. `lm_client.py` was reusing the same TCP connection via the default `requests` session.
- **Fix 1 (`lm_client.py`):** Added `Connection: close` header so each request uses a fresh TCP connection (no keep-alive reuse). Changed `timeout=self.timeout` to `timeout=(10, self.timeout)` — connect fails fast (10s) while read waits the full `LM_STUDIO_TIMEOUT` (300s from settings).
- **Fix 2 (`skills/tasks.py`):** Added `time_limit=360, soft_time_limit=330` to `generate_tree_task` so Celery allows up to 6 minutes per generation attempt.
- **Files Modified:** `backend/core/lm_client.py`, `backend/skills/tasks.py`
- **Breaking Changes:** No
- **Next Agent Notes:** If `RemoteDisconnected` persists under very high load, consider switching to streaming (`stream=True`) with chunked reading. The `LM_STUDIO_TIMEOUT` env var (default 300s) controls the read timeout.

### 2026-07-07 10:09 — Fix: NameError ProtocolTypeRouter in asgi.py
- **Changes Made:**
  - Added missing imports to `backend/core/asgi.py`: `ProtocolTypeRouter`, `URLRouter` from `channels.routing`; `AuthMiddlewareStack` from `channels.auth`; `path` from `django.urls`
- **SOLID Principles Applied:** N/A (import fix)
- **Files Modified:** `backend/core/asgi.py`
- **Bugs Fixed:** `NameError: name 'ProtocolTypeRouter' is not defined` at ASGI startup — the channels routing symbols were used in `application = ProtocolTypeRouter(...)` but never imported at the top of the file
- **Breaking Changes:** No
- **Next Agent Notes:** `asgi.py` now correctly imports all channels routing primitives before use. Import verified via `python -c "import core.asgi"`.
