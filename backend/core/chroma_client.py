"""
ChromaDB Client for RAG-based Code Evaluation
Singleton client managing skill knowledge, code patterns, and AI detection collections.

EmbeddingRecord integration:
    Every upsert calls _sync_embedding_record() to keep the relational
    EmbeddingRecord table in sync with ChromaDB state.
    Every delete calls _delete_embedding_record() to remove orphaned tracking rows.
    This prevents stale vector references after relational model updates.
"""

import hashlib
import logging
from typing import List, Dict, Any, Optional

import chromadb
from chromadb.config import Settings
from django.conf import settings as django_settings

logger = logging.getLogger(__name__)


class ChromaDBClient:
    """
    Singleton ChromaDB client for SkillTree AI.
    Manages three collections:
    - skill_knowledge: Skill descriptions and best practices
    - code_patterns: High-quality code examples per skill
    - ai_code_samples: Known AI-generated patterns for detection
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Initialize ChromaDB persistent client
        self.client = chromadb.PersistentClient(
            path=django_settings.CHROMA_PATH,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Initialize collections
        self.skill_knowledge = self._get_or_create_collection(
            name="skill_knowledge",
            metadata={"description": "Skill descriptions and best practices for RAG context"}
        )
        
        self.code_patterns = self._get_or_create_collection(
            name="code_patterns",
            metadata={"description": "High-quality code examples per skill"}
        )
        
        self.ai_code_samples = self._get_or_create_collection(
            name="ai_code_samples",
            metadata={"description": "Known AI-generated code patterns for detection"}
        )
        
        self._initialized = True
    
    def _get_or_create_collection(self, name: str, metadata: Dict[str, str]):
        """Get existing collection or create new one."""
        try:
            return self.client.get_collection(name=name)
        except Exception:
            return self.client.create_collection(
                name=name,
                metadata=metadata
            )

    def get_collection(self, name: str):
        """Get collection by name."""
        return self.client.get_collection(name=name)

    def clear_collections(self, collection_names: List[str]):
        """Wipe all documents from specified collections and their EmbeddingRecord rows."""
        for name in collection_names:
            try:
                collection = self.get_collection(name)
                results = collection.get()
                ids = results['ids']
                if ids:
                    collection.delete(ids=ids)
                # Remove tracking records for this collection
                self._bulk_delete_embedding_records(name)
            except Exception as exc:
                logger.warning(f"[ChromaDB] clear_collections failed for {name!r}: {exc}")

    # ------------------------------------------------------------------
    # EmbeddingRecord lifecycle helpers
    # ------------------------------------------------------------------

    def _sync_embedding_record(
        self,
        content_type: str,
        object_id: int,
        collection_name: str,
        chroma_id: str,
        document: str,
    ):
        """
        Create or update the relational EmbeddingRecord for a upserted vector.
        Computes SHA-256 of the document text to detect content drift.
        Skips gracefully if called outside a Django app context (e.g. tests).
        """
        try:
            from skills.models import EmbeddingRecord
            checksum = hashlib.sha256(document.encode('utf-8')).hexdigest()
            EmbeddingRecord.objects.update_or_create(
                content_type=content_type,
                object_id=object_id,
                collection_name=collection_name,
                defaults={'chroma_id': chroma_id, 'checksum': checksum},
            )
        except Exception as exc:
            # Non-fatal — log and continue so the vector upsert still succeeds.
            logger.warning(f"[ChromaDB] EmbeddingRecord sync failed ({content_type}#{object_id}): {exc}")

    def _delete_embedding_record(
        self,
        content_type: str,
        object_id: int,
        collection_name: str,
    ):
        """Remove the tracking record when a vector is explicitly deleted."""
        try:
            from skills.models import EmbeddingRecord
            EmbeddingRecord.objects.filter(
                content_type=content_type,
                object_id=object_id,
                collection_name=collection_name,
            ).delete()
        except Exception as exc:
            logger.warning(f"[ChromaDB] EmbeddingRecord delete failed ({content_type}#{object_id}): {exc}")

    def _bulk_delete_embedding_records(self, collection_name: str):
        """Remove all EmbeddingRecord rows for a given collection (used by clear_collections)."""
        try:
            from skills.models import EmbeddingRecord
            EmbeddingRecord.objects.filter(collection_name=collection_name).delete()
        except Exception as exc:
            logger.warning(f"[ChromaDB] Bulk EmbeddingRecord delete failed for {collection_name!r}: {exc}")

    def get_stale_skill_embeddings(self) -> List[int]:
        """
        Return a list of skill IDs whose embedding checksum is stale
        (i.e. the Skill row was updated after the last embed).
        """
        try:
            from skills.models import EmbeddingRecord, Skill
            from django.db.models import F
            stale_records = EmbeddingRecord.objects.filter(
                content_type='skill',
                collection_name='skill_knowledge',
            ).select_related()
            skill_ids = []
            for record in stale_records:
                try:
                    skill = Skill.objects.get(pk=record.object_id)
                    if skill.updated_at > record.updated_at:
                        skill_ids.append(record.object_id)
                except Skill.DoesNotExist:
                    skill_ids.append(record.object_id)  # orphaned
            return skill_ids
        except Exception as exc:
            logger.warning(f"[ChromaDB] get_stale_skill_embeddings failed: {exc}")
            return []

    
    def upsert_skill_knowledge(
        self,
        skill_id: int,
        title: str,
        description: str,
        category: str,
        difficulty: int,
        best_practices: Optional[str] = None
    ):
        """
        Upsert skill knowledge to ChromaDB.
        
        Args:
            skill_id: Unique skill identifier
            title: Skill title
            description: Skill description
            category: Skill category
            difficulty: Difficulty level (1-5)
            best_practices: Optional best practices text
        """
        # Combine text for embedding
        text_parts = [
            f"Skill: {title}",
            f"Category: {category}",
            f"Difficulty: {difficulty}/5",
            f"Description: {description}"
        ]
        
        if best_practices:
            text_parts.append(f"Best Practices: {best_practices}")
        
        document = "\n\n".join(text_parts)
        doc_id = f"skill_{skill_id}"

        # Upsert to ChromaDB
        self.skill_knowledge.upsert(
            ids=[doc_id],
            documents=[document],
            metadatas=[{
                "skill_id": skill_id,
                "title": title,
                "category": category,
                "difficulty": difficulty,
            }]
        )

        # Keep EmbeddingRecord in sync
        self._sync_embedding_record(
            content_type='skill',
            object_id=skill_id,
            collection_name='skill_knowledge',
            chroma_id=doc_id,
            document=document,
        )
    
    def query_skill_knowledge(
        self,
        query_text: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query skill knowledge collection for relevant context.
        
        Args:
            query_text: Code or description to find relevant skills for
            n_results: Number of results to return
            
        Returns:
            List of relevant skill knowledge chunks with metadata
        """
        try:
            results = self.skill_knowledge.query(
                query_texts=[query_text],
                n_results=n_results
            )
            
            # Format results
            formatted = []
            if results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                for i, doc in enumerate(docs):
                    formatted.append({
                        "document": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else 0.0
                    })
            
            return formatted
        except Exception as e:
            logger.warning(f"[ChromaDB] query_skill_knowledge error: {e}")
            return []
    
    def upsert_code_pattern(
        self,
        pattern_id: str,
        code: str,
        language: str,
        skill_id: int,
        description: str,
        quality_score: float = 1.0
    ):
        """
        Upsert high-quality code pattern.
        
        Args:
            pattern_id: Unique pattern identifier
            code: Source code
            language: Programming language
            skill_id: Associated skill ID
            description: Pattern description
            quality_score: Quality rating (0-1)
        """
        document = f"Language: {language}\nDescription: {description}\n\nCode:\n{code}"
        
        self.code_patterns.upsert(
            ids=[pattern_id],
            documents=[document],
            metadatas=[{
                "language": language,
                "skill_id": skill_id,
                "description": description,
                "quality_score": quality_score
            }]
        )
    
    def query_code_patterns(
        self,
        code: str,
        language: str,
        n_results: int = 3
    ) -> List[Dict[str, Any]]:
        """
        Query code patterns for similar high-quality examples.
        
        Args:
            code: Code to find similar patterns for
            language: Programming language
            n_results: Number of results
            
        Returns:
            List of similar code patterns
        """
        try:
            query_text = f"Language: {language}\n\nCode:\n{code}"
            results = self.code_patterns.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"language": language}
            )
            
            formatted = []
            if results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                
                for i, doc in enumerate(docs):
                    formatted.append({
                        "document": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {}
                    })
            
            return formatted
        except Exception:
            return []
    
    def upsert_ai_sample(
        self,
        sample_id: str,
        code: str,
        language: str,
        source: str,
        confidence: float = 1.0
    ):
        """
        Upsert known AI-generated code sample for detection.
        
        Args:
            sample_id: Unique sample identifier
            code: AI-generated code
            language: Programming language
            source: AI source (e.g., "gpt-4", "copilot")
            confidence: Confidence this is AI-generated (0-1)
        """
        document = f"Language: {language}\nSource: {source}\n\nCode:\n{code}"
        
        self.ai_code_samples.upsert(
            ids=[sample_id],
            documents=[document],
            metadatas=[{
                "language": language,
                "source": source,
                "confidence": confidence
            }]
        )
    
    def query_ai_samples(
        self,
        code: str,
        language: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Query AI samples to detect similarity to known AI-generated code.
        
        Args:
            code: Code to check
            language: Programming language
            n_results: Number of results
            
        Returns:
            List of similar AI-generated samples with distances
        """
        try:
            query_text = f"Language: {language}\n\nCode:\n{code}"
            results = self.ai_code_samples.query(
                query_texts=[query_text],
                n_results=n_results,
                where={"language": language}
            )
            
            formatted = []
            if results['documents'] and len(results['documents']) > 0:
                docs = results['documents'][0]
                metadatas = results['metadatas'][0] if results['metadatas'] else []
                distances = results['distances'][0] if results['distances'] else []
                
                for i, doc in enumerate(docs):
                    formatted.append({
                        "document": doc,
                        "metadata": metadatas[i] if i < len(metadatas) else {},
                        "distance": distances[i] if i < len(distances) else 1.0
                    })
            
            return formatted
        except Exception:
            return []
    
    def reset_all_collections(self):
        """Reset all ChromaDB collections and purge all EmbeddingRecord rows."""
        try:
            for name in ["skill_knowledge", "code_patterns", "ai_code_samples"]:
                try:
                    self.client.delete_collection(name)
                except Exception:
                    pass
                self._bulk_delete_embedding_records(name)

            # Recreate empty collections
            self.skill_knowledge = self._get_or_create_collection(
                "skill_knowledge",
                {"description": "Skill descriptions and best practices"}
            )
            self.code_patterns = self._get_or_create_collection(
                "code_patterns",
                {"description": "High-quality code examples"}
            )
            self.ai_code_samples = self._get_or_create_collection(
                "ai_code_samples",
                {"description": "Known AI-generated patterns"}
            )
            logger.info("[ChromaDB] All collections reset successfully.")
        except Exception as e:
            logger.error(f"[ChromaDB] reset_all_collections failed: {e}")
    
    def get_collection_stats(self) -> Dict[str, int]:
        """Get document counts for all collections."""
        return {
            "skill_knowledge": self.skill_knowledge.count(),
            "code_patterns": self.code_patterns.count(),
            "ai_code_samples": self.ai_code_samples.count()
        }


# Singleton instance
chroma_client = ChromaDBClient()


def get_chroma_client():
    """Helper to get the singleton ChromaDB client instance."""
    return chroma_client
