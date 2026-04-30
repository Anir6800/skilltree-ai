<div align="center">
  <img src="https://via.placeholder.com/150" alt="SkillTree AI Logo" width="150" height="150" />
  
  # SkillTree AI
  
  **An immersive, AI-driven gamified learning platform for developers.**
  
  [![Python Version](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://python.org)
  [![Django Version](https://img.shields.io/badge/Django-5.x-092E20.svg)](https://djangoproject.com)
  [![React Version](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev)
  [![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED.svg)](https://docker.com)
  [![Vector DB](https://img.shields.io/badge/ChromaDB-Vector_Store-FF6B6B.svg)](https://trychroma.com)
  [![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
</div>

---

## 1. Project Introduction

**SkillTree AI** is a production-grade, AI-powered gamified learning platform designed to revolutionize developer education. By combining dynamic **skill trees**, an interconnected **quest system**, and an intelligent **AI orchestration pipeline**, the platform delivers a highly personalized, immersive learning experience.

### Vision and Purpose
Traditional learning platforms offer linear, static progression. SkillTree AI breaks this paradigm by employing directed acyclic graphs (DAGs) to map out learning journeys, allowing learners to traverse dynamic skill trees shaped by their abilities. Our goal is to make learning to code as engaging as playing an RPG, powered by state-of-the-art Local AI inference and vector-based semantic search.

### Key Capabilities
- **AI-Driven Curriculum:** Fully automated generation of skill graphs tailored to user goals.
- **RAG-Assisted Evaluation:** AI analyzes code submissions not just for correctness, but for readability, style, and heuristics.
- **Real-Time Multiplayer Arena:** Compete against other developers in real-time coding matches.
- **Plagiarism & AI-Detection:** A sophisticated three-layer detection pipeline using semantic matching, LLM analysis, and heuristic checks.

### Architecture Philosophy
Our architecture follows strict data normalization in the relational database (PostgreSQL), heavily integrates asynchronous processing for expensive AI/Vector operations (Celery + Redis), and implements eventual consistency strategies with our vector store (ChromaDB).

---

## 2. Feature Overview

### AI Skill Tree Generation
The platform leverages LLMs to dynamically generate complex DAGs representing learning paths. Trees start as "stubs" and are progressively hydrated through asynchronous workers, ensuring zero UI blocking during heavy generation phases.

### Quest Progression System
Hands-on coding challenges are tied to specific skill nodes. Quests feature a rigorous evaluation sandbox (Docker) followed by semantic analysis, returning highly detailed feedback to the user and dynamically adjusting future difficulty (Bayesian scoring).

### Semantic Search & ChromaDB Integration
All core textual data (Skills, Quests) is converted to vector embeddings and synchronized with ChromaDB. This powers context-aware retrieval, intelligent RAG pipelines for code evaluation, and similarity matching to detect duplicate content.

### AI Pipeline Orchestration
An asynchronous, event-driven pipeline orchestrates LLM calls to local inference engines (LM Studio). This system handles prompt lifecycles, structured JSON outputs, robust retry handling, and fallback mechanisms on timeout or generation failure.

### Progress Tracking & Achievements
Progression is gamified through XP, Levels (calculated dynamically: `(xp // 500) + 1`), streak counting, and an extensible badge issuance system powered by dynamic JSON criteria.

### Real-Time Synchronization
Powered by Django Channels and Redis, WebSocket connections provide real-time updates for multiplayer coding arenas, leaderboard positioning, and asynchronous task completion (e.g., "Your code has been evaluated!").

### Motion & Glassmorphism Design
The React frontend leverages Three.js for interactive skill node mapping and Framer Motion for buttery-smooth glassmorphic UI interactions, ensuring a premium, immersive user experience.

---

## 3. Architecture Overview

SkillTree AI is distributed across several key services, orchestrated via Docker.

```mermaid
graph TD
    Client((Client App\nReact / Zustand))
    
    subgraph Django Backend
        API[Django REST Framework]
        WS[Django Channels]
        ORM[Django ORM]
    end
    
    subgraph Data Layer
        PG[(PostgreSQL)]
        Redis[(Redis Cache/Broker)]
        Chroma[(ChromaDB Vector Store)]
    end
    
    subgraph AI & Execution Layer
        Celery[Celery Workers]
        LM[LM Studio / LLM API]
        Sandbox[Docker Execution Sandbox]
    end

    Client <-->|HTTPS / REST| API
    Client <-->|WSS| WS
    API <--> ORM
    WS <--> Redis
    ORM <--> PG
    API -->|Offload Task| Redis
    Redis -->|Consume Task| Celery
    Celery <--> LM
    Celery <--> Chroma
    Celery <--> Sandbox
    Celery -.->|Update State| ORM
```

### Request Lifecycle Example (Code Submission)
1. User submits code to `/api/quests/{id}/submit/`.
2. API validates and saves a `QuestSubmission` record, triggering an `ExecutionTask`.
3. Celery worker executes the code in the Docker sandbox.
4. If successful, another task queries ChromaDB for contextual hints, and pings LM Studio for code review.
5. AI results are saved to `EvaluationResult` and `StyleReport`.
6. Frontend is notified via WebSocket.

---

## 4. Tech Stack

### Frontend
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **React** | 19.x | Component-based UI framework |
| **Tailwind CSS** | 4.x | Utility-first styling for glassmorphism |
| **Framer Motion** | 11.x | Advanced micro-animations |
| **Zustand** | 5.x | Lightweight global state management |
| **Three.js / R3F** | Latest | 3D rendering of the Skill Tree |

### Backend & Infrastructure
| Technology | Version | Purpose |
| :--- | :--- | :--- |
| **Django** | 5.x | Core relational backend framework |
| **PostgreSQL** | 16.x | Primary relational source of truth |
| **Redis** | 7.x | Celery broker, cache, WebSocket layer |
| **Celery** | 5.x | Asynchronous task orchestration |
| **ChromaDB** | 0.4.x | Vector database for embeddings |
| **LM Studio** | Local | Local OpenAI-compatible LLM inference |
| **Docker** | Latest | Containerization & isolated execution |

---

## 5. Monorepo Structure

```text
skilltree-ai/
├── backend/                  # Django REST framework backend
│   ├── ai_detection/         # Plagiarism & AI-generation pipelines
│   ├── ai_evaluation/        # RAG and code review logic
│   ├── core/                 # Django settings, celery app, base configs
│   ├── executor/             # Dockerized code sandbox interface
│   ├── quests/               # Quests, submissions, test cases
│   ├── skills/               # Skill models, graphs, vector synchronization
│   ├── users/                # Authentication, profiles, achievements
│   └── manage.py             # Django entrypoint
├── frontend/                 # React frontend application
│   ├── src/
│   │   ├── api/              # Axios instances & interceptors
│   │   ├── components/       # Shared UI, glassmorphic cards
│   │   ├── pages/            # Page layouts (Quest, SkillTree, Arena)
│   │   ├── store/            # Zustand global state
│   │   └── utils/            # Helpers, constants, formatters
├── docs/                     # Comprehensive architecture documentation
│   └── database/             # ERD, schema rules, vector architecture
├── scripts/                  # CI/CD and DB seeding utilities
├── docker-compose.yml        # Production/Dev service orchestration
└── README.md                 # This file
```

---

## 6. Environment Setup

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker Engine & Docker Compose
- LM Studio (if using local AI inference)

### 1. Database & Cache Services
Run the necessary stateful services using Docker:
```bash
docker-compose up -d db redis chromadb
```

### 2. Backend Setup
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

In a separate terminal, start the Celery worker:
```bash
celery -A core worker -l info
```

### 3. Frontend Setup
```bash
cd frontend
npm install
npm run dev
```

### 4. LM Studio Setup
1. Open LM Studio and download an embedding model (e.g., `nomic-embed-text-v1.5`) and a chat model (e.g., `Llama-3-8B-Instruct`).
2. Start the Local Server in LM Studio (default port `1234`).
3. Ensure CORS is enabled in LM Studio settings.

---

## 7. Environment Variables

Create a `.env` file in the `backend/` directory:

| Variable | Description | Required | Default |
| :--- | :--- | :---: | :--- |
| `SECRET_KEY` | Django cryptographic key | Yes | - |
| `DEBUG` | Enable development mode | Yes | `True` |
| `DATABASE_URL` | PostgreSQL connection string | Yes | `postgres://user:pass@localhost:5432/db` |
| `REDIS_URL` | Redis connection string | Yes | `redis://localhost:6379/0` |
| `LM_STUDIO_URL` | Local inference API endpoint | No | `http://localhost:1234/v1` |
| `LM_STUDIO_MODEL` | The LLM to use for generation | No | `llama-3-8b-instruct` |
| `CHROMA_PATH` | Path/URL to ChromaDB instance | Yes | `./chroma_db` |
| `CORS_ALLOWED_ORIGINS` | Permitted frontend origins | Yes | `http://localhost:3000` |

*Security Note: Never commit production `.env` files. Ensure `DEBUG=False` in production to prevent data leakage.*

---

## 8. Development Workflow

- **Database Migrations:** All manual schema changes must be codified into Django migrations. Run `python manage.py makemigrations` after altering models.
- **Code Execution Testing:** The execution module requires Docker running on the host machine to spin up secure isolated containers.
- **Vector Synchronization:** Vector embeddings sync asynchronously. If you need to force sync, run `python manage.py sync_vectors --force`.
- **Cache Invalidation:** Restart the Redis container or run `redis-cli flushall` to clear ephemeral leaderboard/session states during testing.
- **Linting & Formatting:** Python uses `black` and `flake8`. Frontend uses `eslint` and `prettier`.

---

## 9. Database Documentation Summary

Our database strictly adheres to Third Normal Form (3NF) for source-of-truth records, utilizing controlled denormalization via Celery workers for read-heavy frontend metrics.
- **Progression Systems:** Driven by `User`, `QuestSubmission`, and `SkillProgress`. Level boundaries are mathematical derivations `(xp // 500) + 1`.
- **DAG Relationships:** The `SkillPrerequisite` model enforces the Directed Acyclic Graph topology of the Skill Trees.
- **Vector Sync:** The `EmbeddingRecord` polymorphic table hashes source data text. Upon changes, hashes mismatch, triggering asynchronous ChromaDB re-embeddings.

*For full details, see [DATABASE_SCHEMA.md](docs/database/DATABASE_SCHEMA.md) and [VECTOR_DB_ARCHITECTURE.md](docs/database/VECTOR_DB_ARCHITECTURE.md).*

---

## 10. AI Pipeline Documentation

The AI orchestration pipeline is built to handle the inherent unreliability of LLM inference:

```mermaid
stateDiagram-v2
    [*] --> PendingTask
    PendingTask --> PromptCompilation : Worker Picks Up
    PromptCompilation --> RAGContextFetch : Query ChromaDB
    RAGContextFetch --> LLMRequest : POST to LM Studio
    LLMRequest --> JSONValidation
    JSONValidation --> Success : Valid JSON
    JSONValidation --> Retry : Invalid Format/Timeout
    Retry --> LLMRequest : Attempt < Max
    Retry --> Failed : Max Retries
    Success --> SaveToDB
    Failed --> SaveToDB
```

- **Validation:** Pydantic models validate LLM JSON outputs.
- **Fallback Handling:** If structured parsing fails, a heuristic fallback executes regex-based extraction.
- **Semantic Enrichment:** ChromaDB acts as a vector cache for historical student solutions to inject into the LLM context window.

---

## 11. API Documentation Summary

The platform uses a RESTful JSON API via Django REST Framework.
- **Authentication:** JWT Bearer tokens via SimpleJWT. Include `Authorization: Bearer <token>`.
- **Pagination:** Global limit-offset pagination (default 20, max 100).
- **Responses:** Standardized enveloped responses: `{"data": {}, "meta": {}, "error": null}`.

**Sample Request (Evaluate Code):**
```json
POST /api/quests/12/submit/
{
  "code": "def fib(n):\n    if n <= 1: return n\n    return fib(n-1) + fib(n-2)",
  "language": "python"
}
```

**Sample Response:**
```json
{
  "status": "queued",
  "task_id": "c1a2-4f32-8b9a...",
  "message": "Submission received, entering execution sandbox."
}
```

---

## 12. Security Documentation

- **Docker Sandbox Execution:** User code runs inside isolated Alpine Linux containers with strict `mem_limit`, network disabled (`network_mode: none`), and standard timeout boundaries (max 5 seconds).
- **Prompt Injection Defense:** User code is strictly sanitized before injection into system prompts. Instructions explicitly instruct the model to ignore meta-instructions within the code blocks.
- **API Security:** CORS configured strictly. CSRF cookies used where applicable. Rate-limiting enforced via Redis to prevent brute-forcing sandbox evaluations.
- **Data Protection:** All PII is restricted. Hashes are used for vector sync comparisons.

---

## 13. Performance & Scalability

- **Database Indexes:** Compound indexes placed on frequent lookup patterns (e.g., `[user, skill, status]`).
- **Caching:** Leaderboards are stored exclusively in Redis Sorted Sets (`ZADD`, `ZREVRANGE`) ensuring $O(\log(N))$ insertions and blazingly fast global ranking reads.
- **AI Asynchrony:** No AI generation blocks an HTTP thread. Long-polling or WebSockets inform the frontend upon Celery task completion.
- **Vector DB Scaling:** ChromaDB runs as a standalone microservice, easily swappable for a managed service (like Pinecone) in high-scale environments.

---

## 14. Testing Strategy

- **Backend:** `pytest` paired with `factory_boy` for model generation. Unit tests mock the LLM endpoints and Docker engine to ensure fast CI runs.
- **AI Pipeline:** Deterministic prompt tests. We inject known inputs and test the JSON parsing boundaries.
- **Vector DB:** Isolated testing collections ensure test suites don't pollute the dev/prod vector space.
- **Frontend:** Vitest and React Testing Library for component rendering and state logic (Zustand).

---

## 15. Deployment Documentation

### Docker Deployment
The repository includes a production-ready `docker-compose.prod.yml`:
1. Build the images: `docker-compose -f docker-compose.prod.yml build`
2. Run migrations: `docker-compose -f docker-compose.prod.yml run web python manage.py migrate`
3. Bring up stack: `docker-compose -f docker-compose.prod.yml up -d`

### Scaling Considerations
- **Stateless Web:** The Django backend is stateless (sessions in Redis), allowing horizontal scaling behind a Load Balancer.
- **Celery Scaling:** Add more worker nodes to the RabbitMQ/Redis broker queue to process simultaneous code evaluations faster.

---

## 16. Troubleshooting Guide

| Issue | Cause | Fix / Debugging Command |
| :--- | :--- | :--- |
| **Docker Sandbox Fails** | Missing local docker engine context | Ensure Docker Desktop/Engine is running. Check permissions. |
| **AI Timeout (504/408)** | LM Studio overwhelmed or not running | Increase Celery timeout. Check LM studio logs. `curl http://localhost:1234/v1/models` |
| **Vector Desync / Chroma Error** | SQLite lock or stale hash mapping | Run `python manage.py sync_vectors --force` to repair mappings. |
| **Redis Connection Refused** | Redis container down | `docker-compose up -d redis` |
| **Frontend Build Fails** | React 19 / Node mismatch | Ensure Node >= 20. Run `npm ci` to reset node_modules. |
| **Celery Tasks Pending** | Worker not started | Run `celery -A core worker -l info` in a new terminal. |

---

## 17. Developer Onboarding

Welcome to SkillTree AI! To get up to speed:
1. **Read the Architecture Rules:** Start with `docs/database/DATABASE_SCHEMA.md` to understand our 3NF policy.
2. **Understand the Async Flow:** Trace the `/submit/` API endpoint to see how HTTP requests delegate to Celery and subsequently to Docker/LM Studio.
3. **Coding Standards:** We enforce strict separation of concerns. Do not put business logic in Django views; place it in the `/services/` layer.
4. **Contributions:** Never write blocking code in a view. Always use Celery for network I/O to external APIs. Make sure to provide comprehensive docstrings.

---

## 18. Future Scalability Notes

- **Microservice Extraction:** The AI Execution and Sandbox pipelines are decoupled enough to be extracted into Go/Rust microservices for vastly reduced overhead.
- **Cloud Vector Stores:** The `ChromaDBClient` is interface-driven. Moving to Pinecone or Qdrant requires only swapping the implementation class, without touching the `EmbeddingRecord` models.
- **Distributed Event Bus:** Shifting from Redis to Kafka for enterprise-scale event routing of matchmaking and AI events.

---

## 19. Documentation References

For deep dives into specific system modules, refer to the official documentation library:
- 🗄️ [DATABASE_SCHEMA.md](docs/database/DATABASE_SCHEMA.md) - Deep dive into PostgreSQL 3NF.
- 🗺️ [ERD.md](docs/database/ERD.md) - Entity Relationship visual maps.
- 📊 [DATABASE_VISUALIZATION.md](docs/database/DATABASE_VISUALIZATION.md) - State diagrams and flowcharts.
- 🧠 [VECTOR_DB_ARCHITECTURE.md](docs/database/VECTOR_DB_ARCHITECTURE.md) - ChromaDB mapping definitions.
- 🤖 [AI_PIPELINE_STORAGE.md](docs/database/AI_PIPELINE_STORAGE.md) - Prompt lifecycle, retry policies, and schema structures.

---
<div align="center">
  <b>Built with passion for developer education.</b><br>
  <i>Empowering learners to build their own paths.</i>
</div>
