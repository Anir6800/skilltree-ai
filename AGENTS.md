# AGENTS.md

## Project Overview

SkillTree AI is a monorepo for a gamified developer learning platform.

- `frontend/` contains the React 19 + Vite app.
- `backend/` contains a Django backend plus a small Node mail server.
- `docs/` contains architecture and database documentation.
- `scripts/` contains project utilities.
- Root `.env` files and generated local databases exist in the repo; do not commit secrets or generated runtime data.

The README is useful architectural context, but some details may be ahead of or behind the checked-in code. When instructions conflict, prefer the actual source files, package files, settings, and tests in the working tree.

## Common Commands

Run commands from the relevant subdirectory unless noted.

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm run lint
```

### Backend

```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
pytest
```

The backend also includes a Node mail server:

```bash
cd backend
npm install
npm run mail
```

### Supporting Services

Use Docker Compose from the repo root when database, Redis, ChromaDB, or other service dependencies are needed:

```bash
docker-compose up -d
```

## Development Notes

- Keep frontend work inside `frontend/src/` unless changing build, package, or deployment configuration.
- Keep backend business logic out of Django views when an existing service/module boundary is available.
- Add or update Django migrations for model changes.
- Prefer existing API client modules in `frontend/src/api/` over ad hoc fetch calls.
- Prefer existing Zustand stores in `frontend/src/store/` for shared frontend state.
- The UI uses React, Tailwind, Framer Motion, Three.js/R3F, React Flow, and lucide-react; follow nearby component patterns before adding new abstractions.
- The backend uses Django, DRF, Celery, Redis, ChromaDB, and LM Studio/OpenAI-compatible local inference patterns; mock external AI, Docker, and network services in tests when possible.
- Do not edit generated folders such as `node_modules/`, `frontend/dist/`, `.pytest_cache/`, or local database/vector-store files unless explicitly requested.

## Verification

Before handing off changes, run the narrowest relevant checks:

- Frontend UI/code changes: `npm run lint` and `npm run build` from `frontend/`.
- Backend Python changes: targeted `pytest` first, then broader `pytest` when shared behavior changed.
- Django model changes: `python manage.py makemigrations --check --dry-run` or create migrations as appropriate.
- Full-stack or integration changes may require Docker services, Redis, ChromaDB, and LM Studio to be running locally.

If a check cannot run because services or dependencies are unavailable, report the exact command attempted and the blocker.

## Safety Rules

- Never commit `.env` contents, secrets, tokens, local database files, vector-store data, or generated build artifacts.
- Do not revert user changes or unrelated work in a dirty tree.
- Avoid destructive commands such as `git reset --hard`, recursive deletes, or database resets unless explicitly requested.
- Keep changes focused on the requested behavior and the existing project style.
