"""
Onboarding Profile Model
Stores user's personalization data from onboarding flow.
"""

from django.db import models
from django.conf import settings


class OnboardingProfile(models.Model):
    """
    User's onboarding profile with goals, experience, and preferences.
    """
    GOAL_CHOICES = [
        ('job_prep', 'Job Preparation'),
        ('interview', 'Interview Cracker'),
        ('upskill', 'Upskilling'),
        ('passion', 'Passion Project'),
    ]
    
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='onboarding_profile'
    )
    
    # Step 2: Primary Goal
    primary_goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    
    # Step 3: Target Role
    target_role = models.CharField(max_length=200)
    
    # Step 4: Experience Years
    experience_years = models.IntegerField(default=0)
    
    # Step 5: Category Levels (JSON)
    # {"algorithms": "beginner", "ds": "intermediate", ...}
    category_levels = models.JSONField(default=dict)
    
    # Step 6: Selected Interests (JSON)
    # ["arrays", "binary_search", "graphs", ...]
    selected_interests = models.JSONField(default=list)
    
    # Step 7: Weekly Hours
    weekly_hours = models.IntegerField(default=5)
    
    # Metadata
    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # AI Path Generation Status
    path_generated = models.BooleanField(default=False)
    generation_started_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_primary_goal_display()}"
