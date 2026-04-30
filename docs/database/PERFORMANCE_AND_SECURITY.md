# Database Performance & Security Guidelines

This document outlines the operational strategies used to maintain high performance, enforce data security, and ensure the integrity of the SkillTree AI architecture across PostgreSQL, Redis, and ChromaDB.

## 1. Performance Strategies

### A. Indexing
To support fast lookups on a rapidly growing dataset, specific indexing strategies are employed:
- **Primary Keys & Foreign Keys**: Implicitly indexed by PostgreSQL.
- **B-Tree Indexes**: Used on highly queried fields like `User.username`, `Skill.title`, and `Quest.skill_id`.
- **Composite Indexes**: Applied to frequent compound queries, such as filtering `QuestSubmission` by `user_id` and `status`.
- **JSONB Indexing**: GIN (Generalized Inverted Index) indexes are used on `EvaluationResult.feedback` and `StyleReport.style_issues` to allow efficient querying of specific JSON keys without full table scans.

### B. Controlled Denormalization
While the database is primarily in 3NF (Third Normal Form), specific aggregates are denormalized for read performance on the dashboard:
- `User.xp` and `User.level` are updated synchronously.
- `SkillProgress.quest_completion_count` avoids expensive `COUNT()` queries across the `QuestSubmission` table.
These denormalized fields are maintained via robust Django signals to ensure they never drift from the underlying authoritative data.

### C. Caching (Redis)
Redis is heavily utilized to offload read pressure from PostgreSQL:
- **Session & Auth**: JWT token blacklisting and session tracking.
- **Leaderboards**: Sorted Sets (`ZADD`) are used to maintain global and study group XP leaderboards, offering `O(log(N))` performance instead of heavy SQL `ORDER BY` operations.
- **Rate Limiting**: API throttling is backed by Redis to prevent abuse.

### D. Connection Pooling
To prevent connection exhaustion under heavy load (especially from concurrent Celery workers), `PgBouncer` or an equivalent connection pooler should be placed between the Django application and the PostgreSQL instance.

## 2. Security & Data Integrity

### A. Authentication & Authorization
- **JWT**: Stateless JSON Web Tokens are used for authentication.
- **Row-Level Security (RLS)**: While handled at the application layer via Django QuerySets, data isolation ensures users can only access their own `QuestSubmission`, `AdaptiveProfile`, and private `GeneratedSkillTree`.
- **Study Groups**: Membership validation is strictly enforced before allowing access to `StudyGroupMessage` or `StudyGroupGoal` records.

### B. Data Validation
- **Strict typing**: Django models strictly enforce data types (e.g., `PositiveIntegerField` for XP).
- **Constraints**: `UniqueConstraint`s are used extensively (e.g., a user can only have one `AdaptiveProfile`, or one `UserBadge` per badge).
- **API Serializers**: Django REST Framework serializers enforce rigorous validation before any data touches the database, rejecting malformed JSON immediately.

### C. Safe Execution Sandboxing
Because SkillTree AI evaluates user-submitted code:
- **Execution Environments**: Code is never executed directly on the host or the database server. It is run inside isolated, ephemeral Docker containers (or restricted sandboxes) initiated by Celery workers.
- **Resource Limits**: Memory and CPU limits are strictly enforced on the sandbox to prevent fork bombs or memory exhaustion attacks.
- **Network Isolation**: The execution sandbox has zero network access, preventing data exfiltration or internal network scanning.

## 3. Data Retention & Cleanup

To prevent unbounded database growth:
- **Soft Deletes**: Critical user data is soft-deleted to maintain analytical integrity, but flagged to be hidden from the UI.
- **Log Pruning**: `ExecutionTask` logs and `DetectionLog`s older than 90 days are periodically archived or pruned via a Celery beat task.
- **Vector Purging**: Orphaned `EmbeddingRecord`s and their corresponding ChromaDB vectors are swept and deleted to reclaim vector storage space.
