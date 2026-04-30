"""
Quests Domain Models — SkillTree AI
=====================================
Quest         — Learning challenge tied to a Skill
QuestSubmission — User's attempt at a quest
SharedSolution  — Peer-visible passed submission
SolutionComment — Threaded comment on a shared solution
"""

from django.db import models
from django.conf import settings
from skills.models import Skill


# ---------------------------------------------------------------------------
# Quest
# ---------------------------------------------------------------------------

class Quest(models.Model):
    """
    A learning challenge associated with a Skill.

    Type determines evaluation path:
        coding    → code executed against test_cases by the executor service
        debugging → buggy starter_code presented; test_cases verify the fix
        mcq       → test_cases[0]['expected_output'] holds the correct option index

    is_stub = True means the AI generation pipeline created this quest as a
    placeholder; content fields will be populated by QuestAutoFillService.
    Stub quests MUST NOT be shown to users in the frontend quest list.

    xp_reward × difficulty_multiplier = total XP awarded on pass.
    """
    TYPE_CHOICES = [
        ('coding', 'Coding'),
        ('debugging', 'Debugging'),
        ('mcq', 'Multiple Choice'),
    ]

    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='quests')
    type = models.CharField(max_length=20, choices=TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    starter_code = models.TextField(blank=True, default='')
    test_cases = models.JSONField(
        default=list,
        help_text='List of {input, expected_output} dicts. '
                  'For MCQ: [{expected_output: <int 0-3>}].',
    )
    xp_reward = models.IntegerField(default=0)
    estimated_minutes = models.IntegerField(default=15)
    difficulty_multiplier = models.FloatField(default=1.0)
    is_stub = models.BooleanField(
        default=False,
        help_text='True if generated stub — QuestAutoFillService will populate content.',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        indexes = [
            # Primary query: "non-stub quests for skill X of type coding"
            models.Index(fields=['skill', 'type', 'is_stub'], name='quest_skill_type_stub_idx'),
            # Stub detection: "find all unfilled stubs"
            models.Index(fields=['is_stub', 'skill'], name='quest_stub_skill_idx'),
            # Recency / admin tooling
            models.Index(fields=['-created_at'], name='quest_created_at_idx'),
        ]

    def __str__(self):
        stub_marker = ' [STUB]' if self.is_stub else ''
        return f"{self.title} ({self.type}){stub_marker}"


# ---------------------------------------------------------------------------
# Quest Submission
# ---------------------------------------------------------------------------

class QuestSubmission(models.Model):
    """
    A user's attempt at completing a quest.

    Status lifecycle:
        pending → running → passed | failed | flagged

    ai_detection_score: 0.0 (human) to 1.0 (likely AI-generated).
    Flagged when score > threshold (configurable in settings).

    celery_task_id: links submission to the async evaluation Celery task.
    Used to poll status from the frontend and verify task ownership.
    Stored as nullable because synchronous fallback evaluations exist.
    A DB-level index is declared in Meta.indexes (do NOT also set db_index=True
    on the field definition — that creates a duplicate index).

    execution_result JSON structure:
        {output, stderr, exit_code, time_ms, tests_passed, tests_total}

    ai_feedback JSON structure:
        {score: float, summary: str, pros: [str], cons: [str], suggestions: [str]}
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('running', 'Running'),
        ('passed', 'Passed'),
        ('failed', 'Failed'),
        ('flagged', 'Flagged'),
        ('explanation_provided', 'Explanation Provided'),
        ('approved', 'Approved'),
        ('confirmed_ai', 'Confirmed AI'),
    ]

    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('cpp', 'C++'),
        ('java', 'Java'),
        ('go', 'Go'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='submissions')
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='submissions')
    code = models.TextField()
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    execution_result = models.JSONField(default=dict)
    ai_feedback = models.JSONField(default=dict)
    ai_detection_score = models.FloatField(default=0.0)
    explanation = models.TextField(blank=True, default='')
    # Nullable: synchronous fallback evaluations don't dispatch a Celery task.
    # Do NOT add db_index=True here — the Meta.indexes entry below covers it.
    celery_task_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # "show user's submissions for quest X" — primary serializer query
            models.Index(fields=['user', 'quest'], name='submission_user_quest_idx'),
            # "my recent submissions filtered by status" — dashboard query
            models.Index(fields=['user', 'status', '-created_at'], name='submission_user_status_idx'),
            # Celery task ownership lookup — single index only
            models.Index(fields=['celery_task_id'], name='submission_celery_task_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.quest.title} ({self.status})"


# ---------------------------------------------------------------------------
# Social / Peer Review
# ---------------------------------------------------------------------------

class SharedSolution(models.Model):
    """
    A passed submission shared publicly for peer review.
    Only created from QuestSubmissions with status='passed'.

    upvotes is a M2M — never use .count() in a hot loop; prefer
    annotating with Count('upvotes') at the queryset level.
    """
    submission = models.OneToOneField(
        QuestSubmission,
        on_delete=models.CASCADE,
        related_name='shared_solution',
    )
    shared_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='upvoted_solutions',
        blank=True,
    )
    views_count = models.IntegerField(default=0)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['-shared_at'], name='sharedsol_shared_at_idx'),
            # Filter by quest for "all solutions to quest X"
            models.Index(
                fields=['submission'],
                name='sharedsol_submission_idx',
                # Note: submission is a OneToOne so it's already uniquely indexed;
                # this explicit index is redundant and intentionally omitted.
                # The UniqueConstraint from OneToOneField covers it.
            ),
        ]

    def __str__(self):
        author = 'Anonymous' if self.is_anonymous else self.submission.user.username
        return f"{author} — {self.submission.quest.title}"

    def get_upvote_count(self):
        """Return total upvote count. Prefer annotating at queryset level for lists."""
        return self.upvotes.count()


class SolutionComment(models.Model):
    """
    Threaded comment on a shared solution.
    Supports one level of nesting (parent FK to self).
    """
    solution = models.ForeignKey(SharedSolution, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='solution_comments')
    text = models.TextField(max_length=1000)
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            # "load all comments for solution X in thread order"
            models.Index(fields=['solution', 'parent', 'created_at'], name='comment_solution_thread_idx'),
            models.Index(fields=['author'], name='comment_author_idx'),
        ]

    def __str__(self):
        return f"{self.author.username} on {self.solution}"