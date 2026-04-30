# SkillTree AI Entity Relationship Diagrams

This document visualizes the database relationships across the different systems within SkillTree AI.

## 1. User Systems

The User Systems domain manages identity, progression (XP/Level), gamification (badges), collaborative groups, and onboarding profiles.

```mermaid
erDiagram
    USER {
        int id PK
        string username
        string email
        int xp
        int level
        int streak_days
        date last_active
        string role
    }

    ONBOARDING_PROFILE {
        int id PK
        int user_id FK
        string primary_goal
        string target_role
        json category_levels
        json selected_interests
        int weekly_hours
    }

    ADAPTIVE_PROFILE {
        int id PK
        int user_id FK
        float ability_score
        int preferred_difficulty
    }

    ADAPTIVE_ADJUSTMENT_LOG {
        int id PK
        int profile_id FK
        float ability_before
        float ability_after
        string reason
    }

    XP_LOG {
        int id PK
        int user_id FK
        int amount
        string source
        datetime created_at
    }

    BADGE {
        int id PK
        string slug
        string name
        string rarity
        json unlock_condition
    }

    USER_BADGE {
        int id PK
        int user_id FK
        int badge_id FK
        boolean seen
    }

    STUDY_GROUP {
        int id PK
        string invite_code
        string name
        int created_by FK
        int max_members
    }

    STUDY_GROUP_MEMBERSHIP {
        int id PK
        int group_id FK
        int user_id FK
        string role
    }

    USER ||--o| ONBOARDING_PROFILE : "has 1-to-1"
    USER ||--o| ADAPTIVE_PROFILE : "has 1-to-1"
    USER ||--o{ XP_LOG : "has many"
    USER ||--o{ USER_BADGE : "earns many"
    BADGE ||--o{ USER_BADGE : "awarded as many"
    ADAPTIVE_PROFILE ||--o{ ADAPTIVE_ADJUSTMENT_LOG : "logs many"
    USER ||--o{ STUDY_GROUP : "creates many"
    USER ||--o{ STUDY_GROUP_MEMBERSHIP : "joins many"
    STUDY_GROUP ||--o{ STUDY_GROUP_MEMBERSHIP : "has many members"
```

## 2. Skill Tree Systems

The Skill Tree Systems domain manages the DAG (Directed Acyclic Graph) of skills, AI-generated trees, user progression tracking, and dynamically generated curricula.

```mermaid
erDiagram
    GENERATED_SKILL_TREE {
        uuid id PK
        int created_by FK
        string topic
        string status
        json raw_ai_response
        boolean is_public
    }

    SKILL {
        int id PK
        string title
        string category
        int difficulty
        int tree_depth
    }

    SKILL_PREREQUISITE {
        int id PK
        int from_skill_id FK
        int to_skill_id FK
    }

    SKILL_PROGRESS {
        int id PK
        int user_id FK
        int skill_id FK
        string status
        int quest_completion_count
    }

    USER_CURRICULUM {
        int id PK
        int user_id FK
        json weeks
        int weekly_hours
    }

    USER ||--o{ GENERATED_SKILL_TREE : "creates many"
    GENERATED_SKILL_TREE }|--|{ SKILL : "generates many"
    SKILL ||--o{ SKILL_PREREQUISITE : "is required by (from)"
    SKILL ||--o{ SKILL_PREREQUISITE : "requires (to)"
    USER ||--o{ SKILL_PROGRESS : "tracks progress"
    SKILL ||--o{ SKILL_PROGRESS : "has user progress"
    USER ||--o| USER_CURRICULUM : "has 1-to-1"
```

## 3. Quest Systems

The Quest Systems domain tracks individual learning challenges, user submissions, execution results, and peer-reviewed shared solutions.

```mermaid
erDiagram
    QUEST {
        int id PK
        int skill_id FK
        string type
        string title
        boolean is_stub
        int xp_reward
    }

    QUEST_SUBMISSION {
        int id PK
        int user_id FK
        int quest_id FK
        string status
        json execution_result
        string celery_task_id
    }

    SHARED_SOLUTION {
        int id PK
        int submission_id FK
        boolean is_anonymous
        int views_count
    }

    SOLUTION_COMMENT {
        int id PK
        int solution_id FK
        int author_id FK
        int parent_id FK
        string text
    }

    SKILL ||--o{ QUEST : "has many"
    USER ||--o{ QUEST_SUBMISSION : "submits many"
    QUEST ||--o{ QUEST_SUBMISSION : "receives many"
    QUEST_SUBMISSION ||--o| SHARED_SOLUTION : "becomes 1-to-1"
    USER }|--|{ SHARED_SOLUTION : "upvotes many"
    SHARED_SOLUTION ||--o{ SOLUTION_COMMENT : "has many comments"
    USER ||--o{ SOLUTION_COMMENT : "authors many"
    SOLUTION_COMMENT ||--o| SOLUTION_COMMENT : "replies to"
```

## 4. AI & Vector DB Systems

This domain tracks background asynchronous processing (execution and AI generation), AI-driven qualitative feedback, LLM detection, and the relational bridge to the ChromaDB vector store.

```mermaid
erDiagram
    EVALUATION_RESULT {
        int id PK
        int submission_id FK
        boolean passed
        int score
        json feedback
        json test_results
    }

    STYLE_REPORT {
        int id PK
        int submission_id FK
        json style_issues
        json suggestions
        float readability_score
    }

    DETECTION_LOG {
        int id PK
        int submission_id FK
        float ai_probability
        json trigger_phrases
        string flag_reason
    }

    EXECUTION_TASK {
        int id PK
        int submission_id FK
        string celery_task_id
        string status
        text result_log
    }

    EMBEDDING_RECORD {
        int id PK
        string content_type
        int object_id
        string vector_id
        string content_hash
        boolean needs_sync
    }

    QUEST_SUBMISSION ||--o| EVALUATION_RESULT : "has 1-to-1"
    QUEST_SUBMISSION ||--o| STYLE_REPORT : "has 1-to-1"
    QUEST_SUBMISSION ||--o| DETECTION_LOG : "has 1-to-1"
    QUEST_SUBMISSION ||--o{ EXECUTION_TASK : "triggers many"
    
    %% Vector sync is polymorphic, logically linking to Quests/Skills
    QUEST ||--o| EMBEDDING_RECORD : "synced via (polymorphic)"
    SKILL ||--o| EMBEDDING_RECORD : "synced via (polymorphic)"
```
