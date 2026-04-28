from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date

class User(AbstractUser):
    """
    SkillTree AI Custom User model.
    Tracks player progression, XP, and immersive attributes.
    """
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    ]
    
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak_days = models.IntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='student')
    avatar_url = models.CharField(max_length=500, default='', blank=True)

    def save(self, *args, **kwargs):
        # Auto-compute level from XP: level = xp // 500 + 1
        self.level = (self.xp // 500) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} (Lvl {self.level})"

class XPLog(models.Model):
    """
    Log of XP gained by a user. Used for history charts.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_logs')
    amount = models.IntegerField()
    source = models.CharField(max_length=200) # e.g. "Quest: Python Basics"
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]

    def __str__(self):
        return f"{self.user.username} +{self.amount} XP from {self.source}"


class Badge(models.Model):
    """
    Achievement badge definition.
    Defines badge metadata and unlock conditions.
    """
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]

    slug = models.SlugField(unique=True, max_length=100)
    name = models.CharField(max_length=100)
    description = models.TextField()
    icon_emoji = models.CharField(max_length=10)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    unlock_condition = models.JSONField(
        default=dict,
        help_text="Condition to unlock badge: {event_type, criteria}"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rarity', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['rarity']),
        ]

    def __str__(self):
        return f"{self.icon_emoji} {self.name} ({self.rarity})"


class UserBadge(models.Model):
    """
    User's earned badge.
    Tracks when user earned a badge and whether they've seen it.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    earned_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
        indexes = [
            models.Index(fields=['user', 'seen']),
            models.Index(fields=['badge']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.badge.name}"



def get_current_year():
    return date.today().year

class WeeklyReport(models.Model):
    """
    Weekly progress report for a user.
    Generated every Monday with AI narrative and PDF.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_reports')
    week_number = models.IntegerField(help_text='ISO week number (1-53)')
    year = models.IntegerField(default=get_current_year)
    pdf_path = models.CharField(max_length=500, help_text='Path to generated PDF file')
    data = models.JSONField(default=dict, help_text='Collected metrics for the week')
    narrative = models.JSONField(default=dict, help_text='AI-generated narrative sections')
    generated_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-generated_at']
        unique_together = ('user', 'week_number', 'year')
        indexes = [
            models.Index(fields=['user', '-generated_at']),
            models.Index(fields=['week_number', 'year']),
        ]

    def __str__(self):
        return f"{self.user.username} - Week {self.week_number}/{self.year}"

    def mark_viewed(self):
        """Mark report as viewed."""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])


class StudyGroup(models.Model):
    """
    Study group for collaborative learning.
    Members can share goals, chat, and track progress together.
    """
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=6, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    max_members = models.IntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invite_code']),
            models.Index(fields=['created_by']),
        ]

    def __str__(self):
        return f"{self.name} ({self.invite_code})"

    def get_member_count(self):
        """Get current member count."""
        return self.members.count()

    def is_full(self):
        """Check if group is at max capacity."""
        return self.get_member_count() >= self.max_members


class StudyGroupMembership(models.Model):
    """
    Membership record for a user in a study group.
    Tracks role and join date.
    """
    ROLE_CHOICES = [
        ('owner', 'Owner'),
        ('member', 'Member'),
    ]

    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='members')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='study_groups')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='member')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'user')
        ordering = ['-joined_at']
        indexes = [
            models.Index(fields=['group', 'user']),
            models.Index(fields=['user']),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class StudyGroupMessage(models.Model):
    """
    Chat message in a study group.
    Supports real-time messaging via WebSocket.
    """
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_messages')
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
        indexes = [
            models.Index(fields=['group', 'sent_at']),
            models.Index(fields=['sender']),
        ]

    def __str__(self):
        return f"{self.sender.username} in {self.group.name}: {self.text[:50]}"


class StudyGroupGoal(models.Model):
    """
    Shared skill goal for a study group.
    Tracks target date and completion status.
    """
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='goals')
    skill = models.ForeignKey('skills.Skill', on_delete=models.CASCADE, related_name='group_goals')
    target_date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['target_date']
        unique_together = ('group', 'skill')
        indexes = [
            models.Index(fields=['group', 'target_date']),
            models.Index(fields=['skill']),
        ]

    def __str__(self):
        return f"{self.group.name} - {self.skill.title} by {self.target_date}"


# ── Onboarding Models ────────────────────────────────────────────────────────

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
        User,
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
    generated_tree_id = models.UUIDField(null=True, blank=True)
    generated_topic = models.CharField(max_length=200, blank=True, default='')
    
    class Meta:
        ordering = ['-completed_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_primary_goal_display()}"


# ── Adaptive Learning Models ─────────────────────────────────────────────────

class AdaptiveProfile(models.Model):
    """
    Stores adaptive learning profile for a user.
    Tracks ability score, preferred difficulty, and adjustment history.
    """
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='adaptive_profile'
    )
    ability_score = models.FloatField(
        default=0.5,
        help_text="0.0 (struggling) to 1.0 (advanced), updated via Bayesian formula"
    )
    preferred_difficulty = models.IntegerField(
        default=3,
        help_text="Auto-set to ceil(ability_score * 5), range 1-5"
    )
    adjustment_history = models.JSONField(
        default=list,
        help_text="Log of every adjustment with timestamp and reason"
    )
    last_adjusted = models.DateTimeField(
        auto_now=True,
        help_text="Timestamp of last adaptation"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Adaptive Profile"
        verbose_name_plural = "Adaptive Profiles"
        indexes = [
            models.Index(fields=['user']),
            models.Index(fields=['ability_score']),
            models.Index(fields=['preferred_difficulty']),
        ]

    def __str__(self):
        return f"{self.user.username} - Ability: {self.ability_score:.2f}, Difficulty: {self.preferred_difficulty}"


class UserSkillFlag(models.Model):
    """
    Flags for user-skill relationships indicating special states.
    Examples: "too_easy", "struggling", "mastered"
    """
    FLAG_CHOICES = [
        ('too_easy', 'Too Easy'),
        ('struggling', 'Struggling'),
        ('mastered', 'Mastered'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='skill_flags'
    )
    skill = models.ForeignKey(
        'skills.Skill',
        on_delete=models.CASCADE,
        related_name='user_flags'
    )
    flag = models.CharField(
        max_length=20,
        choices=FLAG_CHOICES,
        help_text="Type of flag (too_easy, struggling, mastered)"
    )
    reason = models.TextField(
        blank=True,
        default='',
        help_text="Reason for flagging (e.g., 'Consecutive failures: 3')"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'skill', 'flag')
        verbose_name = "User Skill Flag"
        verbose_name_plural = "User Skill Flags"
        indexes = [
            models.Index(fields=['user', 'flag']),
            models.Index(fields=['skill', 'flag']),
        ]

    def __str__(self):
        return f"{self.user.username} - {self.skill.title}: {self.flag}"
