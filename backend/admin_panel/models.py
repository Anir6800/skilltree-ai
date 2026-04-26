from django.db import models
from django.conf import settings
from skills.models import Skill
from quests.models import Quest


class AdminContent(models.Model):
    """
    Admin-created learning content for skills.
    Can be lessons, tips, examples, or reference material.
    """
    CONTENT_TYPE_CHOICES = [
        ('lesson', 'Lesson'),
        ('tip', 'Tip'),
        ('example', 'Example'),
        ('reference', 'Reference'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('ai_reviewed', 'AI Reviewed'),
        ('published', 'Published'),
    ]
    
    LANGUAGE_CHOICES = [
        ('python', 'Python'),
        ('javascript', 'JavaScript'),
        ('cpp', 'C++'),
        ('java', 'Java'),
        ('go', 'Go'),
        ('sql', 'SQL'),
        ('html', 'HTML'),
        ('css', 'CSS'),
        ('markdown', 'Markdown'),
    ]
    
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='admin_content')
    content_type = models.CharField(max_length=20, choices=CONTENT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    body = models.TextField(help_text='Markdown formatted content')
    code_example = models.TextField(blank=True, default='')
    language = models.CharField(max_length=20, choices=LANGUAGE_CHOICES, default='python')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    ai_review_notes = models.TextField(blank=True, default='', help_text='LM Studio review output')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_content')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['skill', 'status']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.content_type}) - {self.status}"


class AssessmentQuestion(models.Model):
    """
    Assessment questions for quests.
    Supports code challenges, MCQs, and open-ended questions.
    """
    QUESTION_TYPE_CHOICES = [
        ('code', 'Code Challenge'),
        ('mcq', 'Multiple Choice'),
        ('open_ended', 'Open Ended'),
    ]
    
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='assessment_questions')
    question_type = models.CharField(max_length=20, choices=QUESTION_TYPE_CHOICES)
    prompt = models.TextField(help_text='Question text or coding challenge description')
    correct_answer = models.TextField(help_text='For MCQ: correct option. For code: model solution.')
    mcq_options = models.JSONField(default=list, blank=True, help_text='Array of options for MCQ')
    test_cases = models.JSONField(default=list, help_text='Array of test cases: [{input, expected_output, description}]')
    validation_criteria = models.TextField(help_text='Natural language criteria for LM Studio to check')
    points = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['quest', '-created_at']
        indexes = [
            models.Index(fields=['quest', 'question_type']),
        ]
    
    def __str__(self):
        return f"{self.quest.title} - {self.question_type} ({self.points}pts)"
