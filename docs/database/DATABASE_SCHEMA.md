# SkillTree AI Database Schema Overview

## Architecture Overview
The SkillTree AI database architecture is designed to support a highly dynamic, AI-driven learning platform. It is built on PostgreSQL as the primary relational data store, augmented by ChromaDB for vector embeddings and Redis for caching and asynchronous task brokering (via Celery). 

The architecture is divided into five core domains:
1. **Users Domain**: Manages user profiles, XP, badges, collaborative study groups, adaptive ability scoring, and onboarding preferences.
2. **Skills Domain**: Manages the directed acyclic graph (DAG) of learning topics, AI-generated skill trees, and user progress.
3. **Quests Domain**: Handles the learning challenges (coding, debugging, MCQ), user submissions, and peer-reviewed shared solutions.
4. **AI Evaluation Domain**: Logs detailed AI feedback and code style reports for quest submissions.
5. **AI Detection Domain**: Manages the results of plagiarism and AI-generation checks against submissions.

## Database Philosophy
The core database philosophy focuses on strict normalization for truth records, coupled with carefully managed denormalized fields for read performance. The database acts as the single source of truth for application state, while computationally expensive derivations (like skill trees or AI feedback) are processed asynchronously and synchronized back to the relational models.

## Normalization Strategy
The schema follows strong normalization principles:
- **Source of Truth**: Core transactional records like `QuestSubmission` act as the authoritative source of truth for user progress.
- **Controlled Denormalization**: Models like `SkillProgress` and `UserCurriculum` contain denormalized counters (`quest_completion_count`, `time_spent_minutes`, `total_quests`) to optimize expensive dashboard aggregations. These are strictly managed by service layers and background Celery tasks.
- **Data Integrity**: Enforced through explicit foreign keys, cascading deletes for tightly coupled dependencies (e.g., deleting a user deletes their submissions), and unique constraints (e.g., `unique_together` on `SkillPrerequisite` to prevent duplicate edges).

## Scalability Goals
- **JSON Fields for Unstructured Data**: Extensive use of `JSONField` (e.g., in `UserCurriculum`, `EvaluationResult`, `Badge`) to store flexible schema-less data without requiring constant database migrations for new AI features.
- **Asynchronous Offloading**: Heavy operations (AI evaluation, vector embedding generation) do not block database transactions. They are delegated to Celery workers, tracking status through state fields (`status`, `celery_task_id`).
- **Separation of Concerns**: Relational models handle constraints and relations, while semantic search and similarity matching are offloaded entirely to ChromaDB.

## Indexing Strategy
Indexes are strategically placed on access patterns rather than purely on foreign keys:
- **Composite Indexes**: Used extensively for common dashboard queries (e.g., querying `SkillProgress` by `[user, status]` or `QuestSubmission` by `[user, quest]`).
- **Recency Indexes**: `created_at` or `updated_at` indexes exist across most models for efficient sorting and time-series aggregations.
- **State Indexes**: Indexes on fields like `is_stub` or `path_generated` allow background workers to quickly find pending records that require processing.

## AI Pipeline Overview
The AI pipeline tightly integrates with the relational database:
- **Generation**: AI models generate records like `GeneratedSkillTree` and `UserCurriculum`. State transitions (`generating` → `ready` | `failed`) track the asynchronous lifecycle. Quests can be generated as "stubs" (`is_stub=True`) which are populated asynchronously by auto-fill services.
- **Evaluation**: `QuestSubmission` triggers Celery tasks. The task ID is stored (`celery_task_id`) to poll status. Results are populated in structured feedback models (`EvaluationResult`, `StyleReport`, `DetectionLog`).
- **Adaptive Adjustments**: `AdaptiveProfile` leverages Bayesian ability scoring to dynamically adjust difficulty. Every change is normalized and tracked immutably in `AdaptiveAdjustmentLog`.

## Vector Synchronization Overview
SkillTree AI requires seamless synchronization between PostgreSQL and ChromaDB for semantic search and AI context retrieval.
- **The Relational Bridge**: The `EmbeddingRecord` model acts as the bridge. It tracks which relational entities (Skills, Quests, etc.) have been embedded into ChromaDB.
- **Staleness Detection**: `EmbeddingRecord` stores a `checksum` (SHA-256) of the embedded content. When a relational record changes, its new checksum is compared against the `EmbeddingRecord`. A mismatch triggers a background re-embedding task.
- **Eventual Consistency**: This pattern ensures eventual consistency between the relational truth and the vector store while preventing duplicate embeddings.

## System-Wide Relationship Philosophy
- **Directed Acyclic Graphs (DAG)**: Skills and prerequisites form a DAG using the `SkillPrerequisite` through-model. Cycle prevention is enforced at the application service layer.
- **Loose Coupling for AI**: AI models don't blindly overwrite core user data; instead, they populate specific feedback models or generate records in isolation before they are linked to the main graph.
- **Robust References**: Widespread use of `on_delete=models.CASCADE` for dependent records ensures no orphaned data, while `models.SET_NULL` is used for non-critical relationships (like the trigger `quest` in `AdaptiveAdjustmentLog` or `generated_tree` in `OnboardingProfile`) to preserve historical context even if the original entity is deleted.

---

# Core Table Documentation

## 1. Users (`users_user`)

**Purpose**: The central identity and progression model for a learner on SkillTree AI. It acts as a custom `AbstractUser` that integrates authentication, role-based access, and core gamification metrics (XP, level, streak).

**Usage Notes**: 
- The `level` field is strictly derived from `xp`. Never manually update `level`. The formula `(xp // 500) + 1` is enforced at the ORM `save()` override.
- Always use `save(update_fields=['xp', 'streak_days', 'last_active'])` to ensure the override recomputes the level.

### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | BigAutoField | No | - | Primary Key |
| `username` | CharField(150) | No | - | Unique |
| `email` | EmailField(254) | No | - | Unique |
| `xp` | IntegerField | No | `0` | Core progression metric |
| `level` | IntegerField | No | `1` | Auto-calculated on save |
| `streak_days` | IntegerField | No | `0` | Consecutive days with passed quests |
| `last_active` | DateField | Yes | `null` | Used for streak calculation |
| `role` | CharField(20) | No | `'student'` | Choices: student, admin, moderator |
| `avatar_url` | CharField(500) | No | `''` | Profile image path |

### Relationships
- **One-to-One**:
  - `onboarding_profile` (`OnboardingProfile`): Path preferences and goals.
  - `adaptive_profile` (`AdaptiveProfile`): Bayesian ability scoring.
  - `curriculum` (`UserCurriculum`): AI-generated weekly plan.
- **One-to-Many**:
  - `xp_logs` (`XPLog`): Append-only history of XP events.
  - `badges` (`UserBadge`): Badges earned by the user.
  - `weekly_reports` (`WeeklyReport`): AI-generated weekly narratives.
  - `submissions` (`QuestSubmission`): Quests attempted by the user.
  - `skill_progress` (`SkillProgress`): Progression state across skills.
- **Many-to-Many**:
  - `study_groups` (Through `StudyGroupMembership`): Collaborative groups.

### Indexes
- Relies primarily on default Django authentication indexes (`username`, `email`).
- Lookups joining user progression generally place the composite index on the related table (e.g., `skill_progress` uses `[user, status]`).

## 2. SkillTrees (`skills_generatedskilltree`)

**Purpose**: Stores AI-generated skill trees for specific topics. Manages the asynchronous generation lifecycle and links to the resulting skill nodes.

**Usage Notes**:
- Status tracks the generation lifecycle: `generating` → `ready` | `failed`.
- The `raw_ai_response` field captures the raw JSON from the LLM for debugging and re-processing.

### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | UUIDField | No | `uuid4` | Primary Key, not editable |
| `topic` | CharField(200) | No | - | DB Indexed |
| `created_by` | ForeignKey | No | - | `on_delete=CASCADE` to User |
| `is_public` | BooleanField | No | `False` | DB Indexed |
| `raw_ai_response` | JSONField | No | `{}` | Raw LLM output |
| `status` | CharField(20) | No | `'generating'` | Choices: generating, ready, failed |
| `depth` | IntegerField | No | `3` | Tree depth config (1-5) |
| `created_at` | DateTimeField| No | `auto_now_add`| - |
| `updated_at` | DateTimeField| No | `auto_now` | - |

### Relationships
- **Many-to-One (FK)**:
  - `created_by` → `User`: The user who requested generation.
- **Many-to-Many**:
  - `skills_created` → `Skill`: The concrete skills generated for this tree.
- **Reverse Relations**:
  - `onboarding_profiles`: Used if this tree was generated during a user's onboarding (FK from `OnboardingProfile.generated_tree` with `SET_NULL`).

### Indexes
- `gst_user_status_idx`: `[created_by, status]` (Primary access pattern for user's dashboard).
- `gst_public_status_idx`: `[is_public, status]` (Used for exploring public community trees).
- `gst_created_at_idx`: `[-created_at]` (Sorting recency).

## 3. SkillNodes (`skills_skill`)

**Purpose**: Represents a core concept or node in the learning graph. 

**Usage Notes**:
- `category` is a freeform string to support dynamic AI-generated categories (e.g., 'custom_machine_learning'), though admin views may restrict standard choices.
- `tree_depth` starts at 0 for root nodes (no prerequisites) and increases by 1 per hop down the directed graph.

### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | BigAutoField | No | - | Primary Key |
| `title` | CharField(200) | No | - | - |
| `description` | TextField | No | - | - |
| `category` | CharField(50) | No | - | Freeform string for dynamic AI topics |
| `difficulty` | IntegerField | No | `1` | Range 1-5 |
| `tree_depth` | IntegerField | No | `0` | Depth in DAG (0 = root) |
| `xp_required_to_unlock`| IntegerField | No | `0` | - |
| `created_at` | DateTimeField| No | `auto_now_add`| - |
| `updated_at` | DateTimeField| No | `auto_now` | - |

### Relationships
- **Many-to-Many**:
  - `prerequisites` → `Skill` (Self): Directed edges managed through `SkillPrerequisite` (related name: `unlocks`).
- **Reverse Relations**:
  - `generated_from_trees` → `GeneratedSkillTree`: Trees that created this skill.
  - `quests` → `Quest`: Challenges tied to this skill.
  - `user_progress` → `SkillProgress`: Learner progression states for this node.
  - `group_goals` → `StudyGroupGoal`: If a group sets this skill as a learning goal.
  - `user_flags` → `UserSkillFlag`: Adaptive flags (e.g., struggling/mastered).

### Indexes
- `skill_cat_diff_idx`: `[category, difficulty]` (Filtered tree views).
- `skill_depth_diff_idx`: `[tree_depth, difficulty]` (Depth-based rendering).
- `skill_created_at_idx`: `[-created_at]` (Recency/Admin tooling).

## 4. QuestChains / Prerequisite Edges (`skills_skillprerequisite`)

**Purpose**: The explicit through-model acting as the directed edges in the Skill DAG. 

**Usage Notes**:
- Semantics: Completing `from_skill` is required before `to_skill` unlocks.
- A unique constraint prevents duplicate edges.
- Cycle prevention is not enforced at the database level; it is enforced at the application/service layer.

### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | BigAutoField | No | - | Primary Key |
| `from_skill` | ForeignKey | No | - | `on_delete=CASCADE` to Skill |
| `to_skill` | ForeignKey | No | - | `on_delete=CASCADE` to Skill |
| `created_at` | DateTimeField| No | `auto_now_add`| - |

### Constraints & Indexes
- **Unique Constraint**: `unique_together = ('from_skill', 'to_skill')` prevents duplicate DAG edges.
- **Index**: `skillprereq_edge_idx`: `[from_skill, to_skill]` (Edge lookup: "what does skill X unlock?").

## 5. Quests (`quests_quest`)

**Purpose**: Represents a specific learning challenge associated with a Skill.

**Usage Notes**:
- `type` determines the evaluation path: coding, debugging, or mcq.
- `is_stub = True` means the AI generation pipeline created this quest as a placeholder to build the tree structure quickly. Content fields are populated later by the `QuestAutoFillService`. Stubs MUST NOT be shown in the frontend.

### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | BigAutoField | No | - | Primary Key |
| `skill` | ForeignKey | No | - | `on_delete=CASCADE` to Skill |
| `type` | CharField(20) | No | - | Choices: coding, debugging, mcq |
| `title` | CharField(200) | No | - | - |
| `description` | TextField | No | - | - |
| `starter_code` | TextField | Yes | `''` | Initial code presented to user |
| `test_cases` | JSONField | No | `[]` | List of `{input, expected_output}` dicts |
| `xp_reward` | IntegerField | No | `0` | Base XP |
| `estimated_minutes` | IntegerField | No | `15` | Used for curriculum planning |
| `difficulty_multiplier`| FloatField | No | `1.0` | Total XP = `xp_reward` * `multiplier` |
| `is_stub` | BooleanField | No | `False` | True if generated as empty placeholder |
| `created_at` | DateTimeField| No | `auto_now_add`| - |
| `updated_at` | DateTimeField| No | `auto_now` | - |

### Relationships
- **Many-to-One (FK)**:
  - `skill` → `Skill`: The skill this quest teaches.
- **Reverse Relations**:
  - `submissions` → `QuestSubmission`: Attempts by users.
  - `adaptive_adjustments` → `AdaptiveAdjustmentLog`: Difficulty changes triggered by this quest.

### Indexes
- `quest_skill_type_stub_idx`: `[skill, type, is_stub]` (Primary query for active quests).
- `quest_stub_skill_idx`: `[is_stub, skill]` (Stub detection for background population).
- `quest_created_at_idx`: `[-created_at]` (Admin tooling).

## 6. UserProgress (`skills_skillprogress`)

**Purpose**: Tracks a user's journey and completion state through a specific skill.

**Usage Notes**:
- Status lifecycle: `locked` → `available` → `in_progress` → `completed`.
- Denormalized counters (`quest_completion_count`, `time_spent_minutes`, `attempts_count`) are maintained by Celery tasks for fast dashboard rendering. They are NOT authoritative; the authoritative source of truth is the aggregation of `QuestSubmission` records. 

### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | BigAutoField | No | - | Primary Key |
| `user` | ForeignKey | No | - | `on_delete=CASCADE` to User |
| `skill` | ForeignKey | No | - | `on_delete=CASCADE` to Skill |
| `status` | CharField(20) | No | `'locked'` | Choices: locked, available, in_progress, completed |
| `completed_at` | DateTimeField| Yes | `null` | Set when status becomes 'completed' |
| `quest_completion_count`| IntegerField | No | `0` | Denormalized counter |
| `time_spent_minutes` | IntegerField | No | `0` | Denormalized counter |
| `attempts_count` | IntegerField | No | `0` | Denormalized counter |
| `updated_at` | DateTimeField| No | `auto_now` | - |

### Relationships
- **Many-to-One (FK)**:
  - `user` → `User`
  - `skill` → `Skill`

### Constraints & Indexes
- **Unique Constraint**: `unique_together = ('user', 'skill')` prevents duplicate progress records.
- **Indexes**:
  - `skillprog_user_status_idx`: `[user, status]` (Primary access pattern for user's dashboard).
  - `skillprog_user_completed_idx`: `[user, completed_at]` (Completion timeline for analytics).

## 7. Achievements (`users_badge` & `users_userbadge`)

**Purpose**: Gamification system that defines achievable badges and tracks which users have earned them.

**Usage Notes**:
- The `Badge` model acts as a template. Its `unlock_condition` JSON field defines dynamic rule evaluation schemas (e.g., `{"event_type": "streak", "criteria": {"days": 7}}`).
- The `UserBadge` model tracks issuance. `seen = False` is used to drive frontend "new badge" notifications.

### 7.a. Badge Template (`users_badge`)

#### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | BigAutoField | No | - | Primary Key |
| `slug` | SlugField(100)| No | - | Unique identifier |
| `name` | CharField(100) | No | - | - |
| `description` | TextField | No | - | - |
| `icon_emoji` | CharField(10) | No | - | - |
| `rarity` | CharField(20) | No | `'common'` | Choices: common, rare, epic, legendary |
| `unlock_condition`| JSONField | No | `{}` | Structured unlock criteria |
| `created_at` | DateTimeField| No | `auto_now_add`| - |

#### Indexes
- `badge_slug_idx`: `[slug]`
- `badge_rarity_idx`: `[rarity]`

---

### 7.b. UserBadge Issuance (`users_userbadge`)

#### Fields
| Field Name | Data Type | Nullable | Default | Constraints / Notes |
| :--- | :--- | :---: | :--- | :--- |
| `id` | BigAutoField | No | - | Primary Key |
| `user` | ForeignKey | No | - | `on_delete=CASCADE` to User |
| `badge` | ForeignKey | No | - | `on_delete=CASCADE` to Badge |
| `earned_at` | DateTimeField| No | `auto_now_add`| - |
| `seen` | BooleanField | No | `False` | For unread notifications |

#### Relationships
- **Many-to-One (FK)**:
  - `user` → `User`
  - `badge` → `Badge`

#### Constraints & Indexes
- **Unique Constraint**: `unique_together = ('user', 'badge')` ensures a badge is awarded only once per user.
- **Indexes**:
  - `userbadge_user_seen_idx`: `[user, seen]` (Notification indicator query).
  - `userbadge_badge_idx`: `[badge]`

---

# Phase 3: Advanced System Tables & Pipeline Structures

This section documents the advanced tables and structures handling AI requests, evaluation, execution, and vector synchronization. Some structures map directly to Django ORM models, while others (like CacheMappings) are managed via Redis.

## 1. AI Evaluation & Feedback (`ai_evaluation_evaluationresult` & `ai_evaluation_stylereport`)
**Maps to: AIResponses, ValidationLogs**

**Purpose**: Stores the comprehensive feedback generated by the LLM models upon quest submission.
- **Schema Explanation**: `EvaluationResult` stores numerical scores, pros/cons lists, and textual summaries. `StyleReport` handles readability metrics and code styling validation.
- **Lifecycle Role**: Populated asynchronously. Once the `ExecutionTask` confirms the code passes tests, a Celery worker requests AI evaluation and writes to these tables.
- **AI Pipeline Usage**: Stores raw outputs from the generative model formatted as JSON.
- **Performance Considerations**: JSONFields are used to prevent rigid schema migrations when the AI model returns new data formats. 

## 2. AI Detection Logging (`ai_detection_detectionlog`)
**Maps to: Analytics, EventLogs**

**Purpose**: Logs the result of AI-generation detection per submission.
- **Schema Explanation**: Stores `embedding_score`, `llm_score`, and `heuristic_score`, combining them into a `final_score`.
- **Lifecycle Role**: Executed in parallel or pre-evaluation. Submissions exceeding thresholds are flagged.
- **Vector Synchronization**: Integrates directly with ChromaDB to determine if the submission overlaps heavily with known AI responses (embedding score).

## 3. Async Task Execution (`executor_executiontask`)
**Maps to: AIRequests, RetryTracking**

**Purpose**: Tracks code execution requests and asynchronous task status.
- **Schema Explanation**: Contains `task_id` (Celery UUID), `status` (queued, processing, completed, failed), and timing metadata.
- **Lifecycle Role**: Enforces state tracking for potentially long-running or retried executions. Acts as the retry tracking boundary for sandbox evaluations.
- **Performance Considerations**: Indexed heavily on `task_id` and `[submission, status]` for polling from the frontend.

## 4. Vector DB Synchronization (`skills_embeddingrecord`)
**Maps to: Embeddings, SemanticSearchMetadata**

**Purpose**: Maintains a relational mapping of entities synchronized to ChromaDB.
- **Schema Explanation**: Stores `content_type`, `object_id`, `collection_name`, and a SHA-256 `checksum` of the embedded content.
- **Lifecycle Role**: Ensures eventual consistency. Before a database row is sent to ChromaDB, a record is created here. On update, if the new text checksum differs from the stored checksum, a re-embedding task fires.
- **Vector Synchronization**: Acts as the exact mapping table preventing duplicate vectors and orphaned data in the vector store.
- **Performance Considerations**: Prevents redundant API calls to the LLM embedding endpoints by short-circuiting unchanged checksums.

## 5. Cache Mappings (Redis)
**Maps to: CacheMappings**

**Purpose**: Ephemeral storage for fast-read operations, rate limiting, and session state.
- **Schema Explanation**: Managed via structured Redis keys (e.g., `user:{id}:streak_cache`, `submission:{id}:eval_status`).
- **Lifecycle Role**: Offloads dashboard counters and live-polling endpoints.
- **Performance Considerations**: Allows the application to bypass PostgreSQL entirely for high-frequency reads (like checking if an AI evaluation has finished).
