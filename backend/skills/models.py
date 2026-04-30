"""
Skills Domain Models — SkillTree AI
====================================
Skill         — Core skill node in the learning graph
SkillPrerequisite — DAG edge (from_skill → to_skill)
SkillProgress — Per-user progress state for a skill
UserCurriculum — AI-generated weekly learning plan
EmbeddingRecord — Tracks ChromaDB embedding state for any relational entity
"""

from django.db import models
from django.conf import settings
from uuid import uuid4


# ---------------------------------------------------------------------------
# Skill Tree Core
# ---------------------------------------------------------------------------

class GeneratedSkillTree(models.Model):
    """
    AI-generated skill tree for a specific topic.
    Stores generation metadata and links to created skills.

    Status lifecycle:
        generating → ready (success)
        generating → failed (error)
    """
    STATUS_CHOICES = [
        ('generating', 'Generating'),
        ('ready', 'Ready'),
        ('failed', 'Failed'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    topic = models.CharField(max_length=200, db_index=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generated_trees',
    )
    is_public = models.BooleanField(default=False, db_index=True)
    raw_ai_response = models.JSONField(default=dict)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='generating')
    depth = models.IntegerField(default=3, help_text='Tree depth (1-5) used during generation')
    skills_created = models.ManyToManyField('Skill', related_name='generated_from_trees', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # Primary access patterns
            models.Index(fields=['created_by', 'status'], name='gst_user_status_idx'),
            models.Index(fields=['is_public', 'status'], name='gst_public_status_idx'),
            models.Index(fields=['-created_at'], name='gst_created_at_idx'),
        ]

    def __str__(self):
        return f"{self.topic} ({self.status})"


class Skill(models.Model):
    """
    Core Skill node in the SkillTree AI graph.

    Category is stored as a freeform CharField (not a FK to a Category table)
    to support dynamic AI-generated categories such as 'custom_machine_learning'.
    Standard categories are enumerated in CATEGORY_CHOICES for admin tooling only.

    tree_depth — 0 for root nodes (no prerequisites), increases by 1 per hop.
    """
    CATEGORY_CHOICES = [
        ('algorithms', 'Algorithms'),
        ('ds', 'Data Structures'),
        ('systems', 'Systems'),
        ('webdev', 'Web Development'),
        ('aiml', 'AI/ML'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.CharField(max_length=50)
    difficulty = models.IntegerField(default=1, help_text='1 (beginner) to 5 (expert)')
    tree_depth = models.IntegerField(default=0, help_text='Depth level in DAG (0 = root)')
    prerequisites = models.ManyToManyField(
        'self',
        symmetrical=False,
        through='SkillPrerequisite',
        related_name='unlocks',
    )
    xp_required_to_unlock = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Filtered tree views: "show me algorithms skills at difficulty 3"
            models.Index(fields=['category', 'difficulty'], name='skill_cat_diff_idx'),
            # Depth-based rendering: retrieve all skills at a given depth level
            models.Index(fields=['tree_depth', 'difficulty'], name='skill_depth_diff_idx'),
            # Recency (admin and debug tooling)
            models.Index(fields=['-created_at'], name='skill_created_at_idx'),
        ]

    def __str__(self):
        return f"{self.title} ({self.category})"


class SkillPrerequisite(models.Model):
    """
    Explicit through-model for skill prerequisites (DAG edges).

    Semantics: completing `from_skill` is required before `to_skill` unlocks.
    Unique constraint prevents duplicate edges.
    Cycle prevention is enforced at the service layer (DFS check in SkillTreeGeneratorService).
    """
    from_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='prerequisite_edges')
    to_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='dependent_edges')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_skill', 'to_skill')
        indexes = [
            # Edge lookup: "what does skill X unlock?" (outgoing edges)
            models.Index(fields=['from_skill', 'to_skill'], name='skillprereq_edge_idx'),
        ]

    def __str__(self):
        return f"{self.from_skill.title} → {self.to_skill.title}"


class SkillProgress(models.Model):
    """
    Tracks a user's journey through a specific skill.

    Status lifecycle: locked → available → in_progress → completed

    Denormalized counters (quest_completion_count, attempts_count, time_spent_minutes)
    are maintained by the skills.services.award_xp service and Celery tasks.
    They are NOT authoritative — QuestSubmission records are the source of truth.
    Use them only for fast dashboard reads; re-derive from submissions for reporting.
    """
    STATUS_CHOICES = [
        ('locked', 'Locked'),
        ('available', 'Available'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='skill_progress')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='user_progress')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='locked')
    completed_at = models.DateTimeField(null=True, blank=True)
    quest_completion_count = models.IntegerField(default=0, help_text='Denormalized: quests passed for this skill')
    time_spent_minutes = models.IntegerField(default=0, help_text='Denormalized: total time spent on this skill')
    attempts_count = models.IntegerField(default=0, help_text='Denormalized: total quest attempts for this skill')
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'skill')
        indexes = [
            # Primary access: "show me this user's in-progress skills"
            models.Index(fields=['user', 'status'], name='skillprog_user_status_idx'),
            # Completion timeline for analytics
            models.Index(fields=['user', 'completed_at'], name='skillprog_user_completed_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.skill.title} ({self.status})"


class UserCurriculum(models.Model):
    """
    AI-generated weekly learning curriculum for a user.
    Generated from available skills and OnboardingProfile preferences.

    `weeks` JSON structure:
        [{"week": 1, "focus": "Arrays", "quests": [quest_id, ...], "estimated_hours": 5}]

    total_quests is a denormalized counter — recompute from len(sum([w['quests'] for w in weeks])).
    """
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='curriculum',
    )
    weeks = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    target_completion_date = models.DateTimeField(null=True, blank=True)
    weekly_hours = models.IntegerField(default=5)
    total_quests = models.IntegerField(default=0, help_text='Denormalized: recompute from weeks JSON if needed')

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='curriculum_user_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {len(self.weeks)} weeks"


# ---------------------------------------------------------------------------
# ChromaDB Vector Synchronization
# ---------------------------------------------------------------------------

class EmbeddingRecord(models.Model):
    """
    Tracks which relational entities have been embedded in ChromaDB.

    Prevents duplicate embeddings and provides a mechanism to detect stale
    vector references when relational records are updated.

    Usage:
        EmbeddingRecord.objects.get_or_create(
            content_type='skill',
            object_id=skill.id,
            collection_name='skill_knowledge',
        )

    The `checksum` field stores an MD5/SHA256 of the embedded content.
    On content update, compare checksum to determine if re-embedding is needed.

    When a relational record is deleted, its EmbeddingRecord should be deleted
    (handled by cascade if using generic FK pattern, or manual cleanup task).
    """
    COLLECTION_CHOICES = [
        ('skill_knowledge', 'Skill Knowledge'),
        ('code_patterns', 'Code Patterns'),
        ('ai_code_samples', 'AI Code Samples'),
    ]

    content_type = models.CharField(
        max_length=50,
        help_text="Model name: 'skill', 'quest', 'questsubmission', etc.",
    )
    object_id = models.IntegerField(
        help_text='PK of the relational record that was embedded.',
    )
    collection_name = models.CharField(max_length=50, choices=COLLECTION_CHOICES)
    chroma_id = models.CharField(
        max_length=200,
        help_text='The ID used in ChromaDB for this document.',
    )
    embedded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    checksum = models.CharField(
        max_length=64,
        blank=True,
        default='',
        help_text='SHA-256 of the embedded text. Used to detect stale embeddings.',
    )

    class Meta:
        unique_together = ('content_type', 'object_id', 'collection_name')
        indexes = [
            # "Is this skill already embedded in skill_knowledge?"
            models.Index(fields=['content_type', 'object_id'], name='embedding_object_idx'),
            # "Find all stale skill embeddings" (join on updated_at vs Skill.updated_at)
            models.Index(fields=['collection_name', 'updated_at'], name='embedding_collection_idx'),
        ]

    def __str__(self):
        return f"{self.content_type}#{self.object_id} in {self.collection_name}"