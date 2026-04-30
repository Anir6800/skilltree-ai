# SkillTree AI Database & Architecture Visualizations

This document provides system-level visualizations of the core workflows, state machines, and data pipelines in the SkillTree AI architecture. It complements the structural models defined in `DATABASE_SCHEMA.md` and the relationships in `ERD.md` by showing how data moves over time.

## 1. Quest Submission State Machine

The lifecycle of a `QuestSubmission` is strictly managed by state transitions. It begins when a user submits code and moves through asynchronous execution and AI evaluation.

```mermaid
stateDiagram-v2
    [*] --> PENDING : User Submits Code
    PENDING --> EXECUTING : Picked up by Celery
    
    EXECUTING --> EVALUATING : Tests Passed
    EXECUTING --> FAILED : Execution/Syntax Error
    
    EVALUATING --> COMPLETED : AI Feedback Generated
    EVALUATING --> FAILED : AI Service Timeout/Error
    
    COMPLETED --> [*]
    FAILED --> [*]
```

## 2. AI Evaluation Sequence Pipeline

This sequence diagram illustrates the integration between Django, the asynchronous task queue (Celery), the local LLM (LM Studio), and PostgreSQL during a code evaluation.

```mermaid
sequenceDiagram
    participant User
    participant API as Django REST API
    participant DB as PostgreSQL
    participant Worker as Celery Worker
    participant LLM as LM Studio / AI Engine

    User->>API: POST /api/quests/{id}/submit/
    API->>DB: Save QuestSubmission (status: PENDING)
    API->>Worker: Dispatch ExecutionTask
    API-->>User: 202 Accepted (Task ID)
    
    Worker->>DB: Update Task (status: EXECUTING)
    Worker->>Worker: Run Sandboxed Execution
    alt Execution Fails
        Worker->>DB: Update QuestSubmission (status: FAILED)
    else Execution Passes
        Worker->>DB: Update QuestSubmission (status: EVALUATING)
        Worker->>LLM: Prompt: Analyze Code & Style
        LLM-->>Worker: JSON Response (Score, Feedback, Style Issues)
        
        Worker->>DB: Create EvaluationResult
        Worker->>DB: Create StyleReport
        Worker->>DB: Update QuestSubmission (status: COMPLETED)
        Worker->>DB: Update UserProgress / XP
    end
```

## 3. Vector Database Synchronization Workflow

SkillTree AI uses ChromaDB for semantic search across skills and quests. To maintain synchronization between relational PostgreSQL data and the vector store, we use an event-driven hash-checking mechanism via the `EmbeddingRecord` model.

```mermaid
flowchart TD
    A[Model Save Signal \n Quest / Skill] --> B{Calculate SHA-256 Content Hash}
    B --> C{Matches existing EmbeddingRecord?}
    
    C -- Yes --> D[Do Nothing \n Data is Sync'd]
    C -- No --> E[Update EmbeddingRecord \n needs_sync = True]
    
    E --> F[Trigger Async VectorSync Task]
    
    F --> G[Generate Text Embeddings]
    G --> H[Upsert to ChromaDB]
    H --> I[Update EmbeddingRecord \n needs_sync = False]
    I --> J[Vector DB Sync Complete]
```

## 4. Onboarding & Skill Tree Generation Flow

The dynamic generation of learning paths (DAGs) involves creating root configurations, contacting the LLM to generate the curriculum, and parsing the output into relational `Skill` and `SkillPrerequisite` models.

```mermaid
flowchart TD
    Start([User Registration]) --> CreateProfile[Create OnboardingProfile]
    CreateProfile --> UserInput[User Inputs Goals & Target Role]
    UserInput --> GenerateTree[Create GeneratedSkillTree \n status: PENDING]
    
    GenerateTree --> CeleryDAG[Celery: Request DAG from AI]
    
    CeleryDAG --> ParseJSON{Parse LLM JSON}
    ParseJSON -- Success --> CreateSkills[Create Skill Records]
    CreateSkills --> CreateEdges[Create SkillPrerequisite Links]
    CreateEdges --> SetComplete[Update GeneratedSkillTree \n status: COMPLETED]
    
    ParseJSON -- Error --> SetFailed[Update GeneratedSkillTree \n status: FAILED]
    SetFailed --> Retry[Admin/System Retry]
    
    SetComplete --> End([Curriculum Ready])
```
