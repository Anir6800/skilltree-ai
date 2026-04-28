from django.db import models
from django.conf import settings
from skills.models import Skill
from django.contrib.auth import get_user_model

User = get_user_model()

class Quest(models.Model):
    """
    Learning tasks associated with specific skills.
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
    test_cases = models.JSONField(default=list)  # [{input: "...", expected_output: "..."}]
    xp_reward = models.IntegerField(default=0)
    estimated_minutes = models.IntegerField(default=15)
    difficulty_multiplier = models.FloatField(default=1.0)

    def __str__(self):
        return f"{self.title} ({self.type})"

class QuestSubmission(models.Model):
    """
    User attempts at completing quests.
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
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    execution_result = models.JSONField(default=dict)  # {output, stderr, exit_code, time_ms, tests_passed}
    ai_feedback = models.JSONField(default=dict)  # {score, summary, pros, cons, suggestions}
    ai_detection_score = models.FloatField(default=0.0)
    explanation = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'quest']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.quest.title} ({self.status})"


class SharedSolution(models.Model):
    """
    Shared code solution for peer review and learning.
    Only created from passed submissions.
    """
    submission = models.OneToOneField(QuestSubmission, on_delete=models.CASCADE, related_name='shared_solution')
    shared_at = models.DateTimeField(auto_now_add=True)
    upvotes = models.ManyToManyField(User, related_name='upvoted_solutions', blank=True)
    views_count = models.IntegerField(default=0)
    is_anonymous = models.BooleanField(default=False)

    class Meta:
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['-shared_at']),
        ]

    def __str__(self):
        username = 'Anonymous' if self.is_anonymous else self.submission.user.username
        return f"{username} - {self.submission.quest.title}"

    def get_upvote_count(self):
        """Get total upvotes."""
        return self.upvotes.count()


class SolutionComment(models.Model):
    """
    Threaded comments on shared solutions.
    Supports nested replies via parent FK.
    """
    solution = models.ForeignKey(SharedSolution, on_delete=models.CASCADE, related_name='comments')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='solution_comments')
    text = models.TextField(max_length=1000)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, null=True, blank=True, related_name='replies')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['solution', 'created_at']),
            models.Index(fields=['author']),
        ]

    def __str__(self):
        return f"{self.author.username} on {self.solution}"