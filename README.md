# SkillTree AI - Immersive Developer Learning Platform

A gamified, AI-powered developer learning platform that combines skill trees, real-time multiplayer, and intelligent code evaluation to create an engaging educational experience.

## 🌟 Features

### Core Learning System
- **Skill Tree Architecture** - Visual progression system with DAG-based prerequisites
- **Quest-Based Learning** - Hands-on coding challenges with automated testing
- **XP & Leveling** - Player progression with 500 XP per level threshold
- **Daily Streaks** - Consistency rewards with streak tracking
- **Personalized Curriculum** - AI-generated weekly learning plans

### AI-Powered Evaluation
- **Three-Layer AI Detection** - Embedding similarity (35%), LLM classification (45%), heuristic analysis (20%)
- **RAG-Based Code Evaluation** - ChromaDB context retrieval with LM Studio integration
- **Automated Code Execution** - Secure Docker sandbox for Python, JavaScript, C++, Java, Go
- **AI Feedback Engine** - Detailed code quality analysis with pros/cons/suggestions

### Multiplayer & Social
- **Real-Time Arena** - Competitive coding matches with WebSocket support
- **Leaderboard System** - Redis-backed global and weekly rankings
- **Mentor System** - AI-driven hints and explanations
- **Match History** - Track performance across all encounters

### Admin & Content Management
- **Admin Panel** - Full CRUD for skills, quests, and content
- **Assessment Engine** - MCQ, code challenges, and open-ended questions
- **Content Review** - AI-assisted content quality validation
- **Flagged Submissions** - AI cheating detection workflow with admin review

## 🛠 Technology Stack

### Backend (Django)
- **Framework**: Django 5.x with Channels for WebSockets
- **Database**: PostgreSQL (production) / SQLite (development)
- **Caching**: Redis for leaderboards and sessions
- **Task Queue**: Celery for async processing
- **AI Integration**: LM Studio (OpenAI-compatible API)
- **Vector DB**: ChromaDB for RAG-based code evaluation
- **Authentication**: JWT (SimpleJWT) with token refresh
- **Code Execution**: Docker sandbox with resource limits
- **API**: Django REST Framework

### Frontend (React)
- **Framework**: React 19 with React Router v7
- **Styling**: Tailwind CSS 4 with custom animations
- **3D Graphics**: Three.js with React Three Fiber
- **State Management**: Zustand
- **UI Library**: Custom components with Framer Motion
- **Code Editor**: Monaco Editor
- **Real-Time**: WebSocket connections for multiplayer

### DevOps & Infrastructure
- **Containerization**: Docker for code execution
- **Deployment**: Production-ready with security headers
- **Environment**: .env-based configuration
- **Monitoring**: Celery beat for scheduled tasks

## 📁 Project Structure

```
skilltree-ai/
├── backend/
│   ├── admin_panel/          # Admin content & assessment management
│   ├── ai_detection/         # Three-layer AI code detection
│   ├── ai_evaluation/        # RAG-based code evaluation
│   ├── auth_app/             # User authentication & JWT
│   ├── core/                 # Django settings, Celery, clients
│   ├── executor/             # Code execution pipeline
│   ├── leaderboard/          # Redis-backed rankings
│   ├── mentor/               # AI mentoring system
│   ├── multiplayer/          # Real-time matches
│   ├── quests/               # Quest & submission models
│   ├── skills/               # Skill tree & progress
│   ├── users/                # Custom user model & profiles
│   └── manage.py
├── frontend/
│   ├── src/
│   │   ├── api/              # API clients
│   │   ├── components/       # Reusable UI components
│   │   ├── pages/            # Page components
│   │   ├── store/            # Zustand state stores
│   │   ├── hooks/            # Custom React hooks
│   │   └── utils/            # Utilities & constants
│   └── package.json
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.12+
- Node.js 20+
- Docker (for code execution)
- PostgreSQL (optional, SQLite works for dev)
- Redis (optional, in-memory for dev)
- LM Studio (for AI features)

### Installation

#### Backend
```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

#### Frontend
```bash
cd frontend
npm install
npm run dev
```

### Environment Variables (.env)
```env
# Django
SECRET_KEY=your-secret-key
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/skilltree

# Redis
REDIS_URL=redis://localhost:6379/0
USE_REDIS_CHANNELS=True

# LM Studio
LM_STUDIO_URL=http://localhost:1234/v1
LM_STUDIO_MODEL=openai/gpt-oss-20b

# ChromaDB
CHROMA_PATH=./chroma_db

# Security
SECURE_SSL_REDIRECT=False
SESSION_COOKIE_SECURE=False
CSRF_COOKIE_SECURE=False

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:3000
```

## 🎮 Key Workflows

### Code Submission Pipeline
1. User submits code via quest or assessment
2. Celery task triggers: `evaluate_submission`
3. Docker sandbox executes test cases
4. LM Studio provides AI code quality feedback
5. Three-layer AI detection runs
6. XP awarded if passed (first-time only)
7. Leaderboard score updated
8. WebSocket notification sent

### AI Detection Pipeline
1. **Layer 1**: Embedding similarity (ChromaDB) - 35%
2. **Layer 2**: LLM classification - 45%
3. **Layer 3**: Heuristic analysis - 20%
4. Final score > 70% → Flagged for admin review
5. Admin can approve (award XP) or override (revoke XP)

### Assessment Evaluation
- **MCQ**: Instant comparison with correct answer
- **Code**: Docker execution with test case pass rate
- **Open-Ended**: LM Studio semantic analysis against criteria

## 📊 Database Models

### Core Models
- **User** - Custom auth with XP, level, streak
- **Skill** - Learning nodes with prerequisites (DAG)
- **Quest** - Coding challenges with test cases
- **QuestSubmission** - User attempts with execution results

### AI Models
- **DetectionLog** - AI detection results per submission
- **EvaluationResult** - Detailed AI feedback

### Admin Models
- **AdminContent** - Learning content with AI review
- **AssessmentQuestion** - MCQ, code, open-ended questions
- **AssessmentSubmission** - User answers with evaluation

### Multiplayer Models
- **Match** - Real-time competitive sessions
- **MatchParticipant** - Player participation tracking

### Leaderboard Models
- **LeaderboardSnapshot** - Historical rankings

## 🔌 API Endpoints

### Authentication
- `POST /api/token/` - Login
- `POST /api/token/refresh/` - Refresh token
- `POST /api/auth/register/` - Register

### Skills & Quests
- `GET /api/skills/` - List skills
- `GET /api/skills/{id}/` - Skill details
- `GET /api/quests/` - List quests
- `POST /api/quests/{id}/submit/` - Submit code

### Execution
- `POST /api/execute/` - Execute code
- `POST /api/execute/test/` - Run test cases
- `GET /api/execute/status/{id}/` - Check status

### Multiplayer
- `GET /api/matches/` - List matches
- `POST /api/matches/` - Create match
- `POST /api/matches/join/` - Join match

### Leaderboard
- `GET /api/leaderboard/` - Global rankings
- `GET /api/leaderboard/weekly/` - Weekly rankings
- `GET /api/leaderboard/my-rank/` - User rank

### Admin
- `GET /api/admin/skills/` - Skill management
- `GET /api/admin/quests/` - Quest management
- `POST /api/admin/submissions/{id}/review/` - Review flagged

### AI Detection
- `GET /api/ai-detection/admin/flagged-submissions/` - List flagged
- `POST /api/ai-detection/submissions/{id}/explain/` - Submit explanation

## 🎨 Frontend Features

### Visual Design
- 3D skill nexus with Three.js
- Framer Motion animations
- Glassmorphism UI
- Gradient text effects
- Responsive sidebar navigation

### Pages
- **Dashboard** - Overview with stats
- **Skill Tree** - Interactive DAG visualization
- **Quest Page** - Code editor with Monaco
- **Arena** - Real-time multiplayer
- **Leaderboard** - Top players
- **Mentor** - AI chat assistant
- **Admin Panel** - Content management

## 🧪 Testing

### Backend
```bash
cd backend
python manage.py test
```

### Frontend
```bash
cd frontend
npm run test
npm run lint
```

## 📝 Development

### Code Quality
- Python: Black, isort, flake8
- JavaScript: ESLint, Prettier
- Type hints: Python, TypeScript (optional)

### Deployment
- Production: `DEBUG=False`, `SECURE_SSL_REDIRECT=True`
- Static files: `python manage.py collectstatic`
- Database: PostgreSQL recommended
- Redis: Required for production leaderboards

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Run tests
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

- LM Studio for AI inference
- ChromaDB for vector storage
- Django, React, and the open-source community

---

**Built with passion for developer education and gamified learning**
