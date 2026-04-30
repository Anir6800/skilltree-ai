# Vector Database Architecture

SkillTree AI integrates an advanced Vector Database layer (powered by ChromaDB) alongside the primary relational database (PostgreSQL). This document details how vector embeddings are generated, managed, and synchronized to enable semantic search, AI-driven quest matching, and dynamic curriculum generation.

## 1. System Overview

- **Engine**: ChromaDB
- **Relational Bridge**: Django Model `EmbeddingRecord`
- **Embedding Model**: Configurable (OpenAI `text-embedding-ada-002` or local equivalent via LM Studio)
- **Primary Use Cases**:
  - Semantic similarity search for related Skills.
  - Contextual retrieval for AI evaluation prompts.
  - Deduplication of dynamically generated Quests.

## 2. Collections Structure

ChromaDB data is partitioned into specific collections based on the domain:

1. **`skills_collection`**: Contains embeddings of skill titles, descriptions, and categories.
2. **`quests_collection`**: Contains embeddings of quest titles, objectives, and code stubs.
3. **`solutions_collection`**: (Future) Embeddings of user code solutions to detect plagiarism or group similar approaches.

## 3. The `EmbeddingRecord` Relational Bridge

Because ChromaDB is a pure vector store, it lacks relational guarantees. We maintain integrity using the `EmbeddingRecord` model in PostgreSQL, which acts as a polymorphic bridge.

### Model Definition (Conceptual)

```python
class EmbeddingRecord(models.Model):
    content_type = ForeignKey(ContentType)  # 'Quest' or 'Skill'
    object_id = PositiveIntegerField()      # ID in Postgres
    content_object = GenericForeignKey()    # The actual instance
    
    vector_id = CharField()                 # UUID in ChromaDB
    content_hash = CharField()              # SHA-256 hash of the text
    needs_sync = BooleanField(default=True) # Sync flag
```

### Hash-Based Synchronization

We employ a strictly event-driven synchronization model to ensure the Vector DB never drifts from the SQL DB.

1. **Content Hashing**: Whenever a `Skill` or `Quest` is saved, a `post_save` signal computes a SHA-256 hash of its core textual fields (e.g., `hash(title + description)`).
2. **Comparison**: It compares this hash against the `content_hash` in the corresponding `EmbeddingRecord`.
3. **Flagging**: If the hash differs (or the record is new), `needs_sync` is set to `True`.
4. **Processing**: A Celery beat task periodically sweeps for `needs_sync=True` records, generates new embeddings, upserts them to ChromaDB, and clears the flag.

## 4. Synchronization Lifecycle (Visualized)

*(See `DATABASE_VISUALIZATION.md` for the Mermaid flowchart of this lifecycle)*

### Fallback & Healing Mechanisms

- **Orphan Sweeper**: A nightly task checks ChromaDB for `vector_id`s that no longer exist in the `EmbeddingRecord` table (due to hard deletes in PostgreSQL) and purges them.
- **Forced Re-index**: A management command (`python manage.py sync_vectors --force`) can bulk recalculate all hashes and regenerate all embeddings, useful when migrating embedding models (e.g., from Ada to an open-source model).

## 5. Query and Retrieval Flow

When the AI Engine needs context (Retrieval-Augmented Generation / RAG):

1. **Query Formulation**: The user's context (e.g., "I want to learn Python async patterns") is converted to an embedding.
2. **Vector Search**: ChromaDB is queried against the `skills_collection` using Cosine Similarity.
3. **Hydration**: ChromaDB returns the top `K` results containing the `vector_id`s and metadata.
4. **Relational Join**: The backend uses the `vector_id`s to fetch the authoritative, up-to-date relational models (e.g., `Skill` objects) from PostgreSQL.
5. **Prompt Injection**: The hydrated relational data is injected into the prompt for the LLM.

## 6. Performance & Scaling Considerations

- **Asynchronous Embeddings**: Embedding generation is strictly handled by Celery workers to avoid blocking HTTP requests.
- **Batch Processing**: The sync task batches API calls to the embedding model (e.g., 100 records at a time) to prevent rate limits and optimize throughput.
- **Local Fallback**: For development or isolated environments, the system can point to a local embedding endpoint served by LM Studio.
