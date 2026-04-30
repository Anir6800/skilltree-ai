"""
Users Domain Models — SkillTree AI
=====================================
User                    — Custom AbstractUser with XP/level/streak
XPLog                   — Append-only XP event log
Badge / UserBadge       — Achievement badge system
WeeklyReport            — AI-generated weekly progress narrative
StudyGroup              — Collaborative group with goals and chat
OnboardingProfile       — User's onboarding data and AI path preferences
AdaptiveProfile         — Bayesian ability scoring for difficulty adaptation
AdaptiveAdjustmentLog   — Normalized log of every adaptive profile change
UserSkillFlag           — Flags per user-skill relationship (struggling, mastered, etc.)
"""

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
from django.utils import timezone
from datetime import date


def get_current_year():
    return date.today().year


# ---------------------------------------------------------------------------
# Core User
# ---------------------------------------------------------------------------

class User(AbstractUser):
    """
    SkillTree AI custom user model.

    XP / Level:
        level is ALWAYS computed from xp via save() override:
            level = (xp // 500) + 1
        NEVER call save(update_fields=['xp', 'level']) — it bypasses the override.
        Always call save() or save(update_fields=['xp', 'streak_days', 'last_active'])
        and let the override recompute level.

    Streak:
        streak_days — consecutive calendar days with at least one passed quest.
        last_active — date of last quest pass. Used to detect streak breaks.
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
        # Invariant: level is always derived from XP.
        # This must run on every save — never bypass with update_fields=['level'].
        self.level = (self.xp // 500) + 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} (Lvl {self.level})"


# ---------------------------------------------------------------------------
# XP Event Log
# ---------------------------------------------------------------------------

class XPLog(models.Model):
    """
    Append-only log of XP events per user.
    Used for history charts and auditing.
    Never update or delete rows — always append.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='xp_logs')
    amount = models.IntegerField()
    source = models.CharField(max_length=200, help_text='e.g. "Quest: Python Basics"')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', '-created_at'], name='xplog_user_created_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} +{self.amount} XP — {self.source}"


# ---------------------------------------------------------------------------
# Badge System
# ---------------------------------------------------------------------------

class Badge(models.Model):
    """
    Badge definition — the template for an achievable badge.

    unlock_condition JSON structure:
        {"event_type": "quest_pass", "criteria": {"count": 10}}
        {"event_type": "streak", "criteria": {"days": 7}}
        {"event_type": "skill_complete", "criteria": {"category": "algorithms"}}
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
        help_text='Structured unlock condition — see docstring for schema.',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['rarity', 'name']
        indexes = [
            models.Index(fields=['slug'], name='badge_slug_idx'),
            models.Index(fields=['rarity'], name='badge_rarity_idx'),
        ]

    def __str__(self):
        return f"{self.icon_emoji} {self.name} ({self.rarity})"


class UserBadge(models.Model):
    """
    A badge earned by a user.
    `seen = False` drives the "new badge" notification indicator.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='badges')
    badge = models.ForeignKey(Badge, on_delete=models.CASCADE, related_name='user_badges')
    earned_at = models.DateTimeField(auto_now_add=True)
    seen = models.BooleanField(default=False)

    class Meta:
        unique_together = ('user', 'badge')
        ordering = ['-earned_at']
        indexes = [
            # "show unseen badges for user" — notification indicator query
            models.Index(fields=['user', 'seen'], name='userbadge_user_seen_idx'),
            models.Index(fields=['badge'], name='userbadge_badge_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.badge.name}"


# ---------------------------------------------------------------------------
# Weekly Report
# ---------------------------------------------------------------------------

class WeeklyReport(models.Model):
    """
    AI-generated weekly learning summary for a user.
    Generated every Monday; `pdf_path` is relative to MEDIA_ROOT.

    data JSON: collected metrics snapshot for the week.
    narrative JSON: AI-generated sections (summary, highlights, challenges).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='weekly_reports')
    week_number = models.IntegerField(help_text='ISO week number (1-53)')
    year = models.IntegerField(default=get_current_year)
    pdf_path = models.CharField(
        max_length=500,
        blank=True,
        default='',
        help_text='Relative path to generated PDF under MEDIA_ROOT. Empty if PDF not yet generated.',
    )
    data = models.JSONField(default=dict, help_text='Collected metrics for the week')
    narrative = models.JSONField(default=dict, help_text='AI-generated narrative sections')
    generated_at = models.DateTimeField(auto_now_add=True)
    viewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-generated_at']
        unique_together = ('user', 'week_number', 'year')
        indexes = [
            models.Index(fields=['user', '-generated_at'], name='weeklyreport_user_idx'),
            models.Index(fields=['week_number', 'year'], name='weeklyreport_week_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — Week {self.week_number}/{self.year}"

    def mark_viewed(self):
        """Mark report as viewed (idempotent)."""
        if not self.viewed_at:
            self.viewed_at = timezone.now()
            self.save(update_fields=['viewed_at'])


# ---------------------------------------------------------------------------
# Study Groups
# ---------------------------------------------------------------------------

class StudyGroup(models.Model):
    """
    Collaborative study group.
    invite_code — 6-character alphanumeric, globally unique.
    """
    name = models.CharField(max_length=100)
    invite_code = models.CharField(max_length=6, unique=True, db_index=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_groups')
    max_members = models.IntegerField(default=6)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['invite_code'], name='studygroup_code_idx'),
            models.Index(fields=['created_by'], name='studygroup_creator_idx'),
        ]

    def __str__(self):
        return f"{self.name} ({self.invite_code})"

    def get_member_count(self):
        return self.members.count()

    def is_full(self):
        return self.get_member_count() >= self.max_members


class StudyGroupMembership(models.Model):
    """
    Through-model for User ↔ StudyGroup.
    role: 'owner' for the group creator, 'member' for everyone else.
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
            models.Index(fields=['group', 'user'], name='membership_group_user_idx'),
            models.Index(fields=['user'], name='membership_user_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} in {self.group.name} ({self.role})"


class StudyGroupMessage(models.Model):
    """
    Chat message in a study group.
    Supports real-time delivery via Django Channels WebSocket consumers.
    """
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='group_messages')
    text = models.TextField()
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['sent_at']
        indexes = [
            # Chronological message load for a group (primary access pattern)
            models.Index(fields=['group', 'sent_at'], name='groupmsg_group_sent_idx'),
            models.Index(fields=['sender'], name='groupmsg_sender_idx'),
        ]

    def __str__(self):
        return f"{self.sender.username} in {self.group.name}: {self.text[:50]}"


class StudyGroupGoal(models.Model):
    """
    A shared skill-learning goal for a study group.
    A group can only have one active goal per skill.
    """
    group = models.ForeignKey(StudyGroup, on_delete=models.CASCADE, related_name='goals')
    skill = models.ForeignKey('skills.Skill', on_delete=models.CASCADE, related_name='group_goals')
    target_date = models.DateField()
    completed = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('group', 'skill')
        ordering = ['target_date']
        indexes = [
            models.Index(fields=['group', 'target_date'], name='groupgoal_group_date_idx'),
            models.Index(fields=['skill'], name='groupgoal_skill_idx'),
        ]

    def __str__(self):
        return f"{self.group.name} — {self.skill.title} by {self.target_date}"


# ---------------------------------------------------------------------------
# Onboarding
# ---------------------------------------------------------------------------

class OnboardingProfile(models.Model):
    """
    User's onboarding preferences, goals, and AI path generation state.

    generated_tree: FK (not a raw UUID) to GeneratedSkillTree, so DB enforces
    referential integrity. SET_NULL on delete prevents orphaned UUID references.

    category_levels JSON:
        {"algorithms": "beginner", "ds": "intermediate", "webdev": "advanced", ...}

    selected_interests JSON:
        ["arrays", "binary_search", "graphs", ...]
    """
    GOAL_CHOICES = [
        ('job_prep', 'Job Preparation'),
        ('interview', 'Interview Cracker'),
        ('upskill', 'Upskilling'),
        ('passion', 'Passion Project'),
    ]

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='onboarding_profile')
    primary_goal = models.CharField(max_length=20, choices=GOAL_CHOICES)
    target_role = models.CharField(max_length=200)
    experience_years = models.IntegerField(default=0)
    category_levels = models.JSONField(default=dict)
    selected_interests = models.JSONField(default=list)
    weekly_hours = models.IntegerField(default=5)
    completed_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # AI path generation state
    path_generated = models.BooleanField(default=False)
    generation_started_at = models.DateTimeField(null=True, blank=True)

    # FK to GeneratedSkillTree — replaces the old raw UUIDField.
    # SET_NULL ensures this doesn't break if the tree is deleted.
    generated_tree = models.ForeignKey(
        'skills.GeneratedSkillTree',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='onboarding_profiles',
        help_text='The AI-generated skill tree created during onboarding.',
    )
    generated_topic = models.CharField(max_length=200, blank=True, default='')

    class Meta:
        ordering = ['-completed_at']
        indexes = [
            models.Index(fields=['user'], name='onboarding_user_idx'),
            # "find onboarding profiles whose tree is still generating"
            models.Index(fields=['generated_tree', 'path_generated'], name='onboarding_tree_status_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.get_primary_goal_display()}"


# ---------------------------------------------------------------------------
# Adaptive Learning
# ---------------------------------------------------------------------------

class AdaptiveProfile(models.Model):
    """
    Bayesian ability scoring for adaptive difficulty selection.

    ability_score: 0.0 (struggling) to 1.0 (advanced).
    preferred_difficulty: ceil(ability_score × 5), range 1-5.
    Adjustment history is normalized to AdaptiveAdjustmentLog (not stored inline).
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='adaptive_profile')
    ability_score = models.FloatField(
        default=0.5,
        help_text='0.0 (struggling) to 1.0 (advanced). Updated via Bayesian formula.',
    )
    preferred_difficulty = models.IntegerField(
        default=3,
        help_text='Auto-set to ceil(ability_score × 5). Range 1-5.',
    )
    last_adjusted = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Adaptive Profile'
        verbose_name_plural = 'Adaptive Profiles'
        indexes = [
            models.Index(fields=['ability_score'], name='adaptive_ability_idx'),
            models.Index(fields=['preferred_difficulty'], name='adaptive_difficulty_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — ability={self.ability_score:.2f} diff={self.preferred_difficulty}"


class AdaptiveAdjustmentLog(models.Model):
    """
    Normalized log of every adaptive profile adjustment.

    Replaces the unbounded `adjustment_history` JSON list that was stored
    directly on AdaptiveProfile. This table supports:
        - paginated adjustment history reads
        - filtering by reason or quest
        - analytics on difficulty progression over time

    quest: nullable FK — some adjustments are triggered by time-based factors
    rather than a specific quest.
    """
    profile = models.ForeignKey(
        AdaptiveProfile,
        on_delete=models.CASCADE,
        related_name='adjustment_logs',
    )
    ability_before = models.FloatField()
    ability_after = models.FloatField()
    difficulty_before = models.IntegerField()
    difficulty_after = models.IntegerField()
    reason = models.CharField(
        max_length=200,
        help_text='e.g. "Consecutive failures: 3" or "Streak: 7 days"',
    )
    quest = models.ForeignKey(
        'quests.Quest',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='adaptive_adjustments',
        help_text='The quest that triggered this adjustment (if any).',
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            # "show adjustment history for this user's profile"
            models.Index(fields=['profile', '-created_at'], name='adaptlog_profile_idx'),
            # "what adjustments were triggered by quest X?"
            models.Index(fields=['quest'], name='adaptlog_quest_idx'),
        ]

    def __str__(self):
        return (
            f"{self.profile.user.username}: "
            f"{self.ability_before:.2f}→{self.ability_after:.2f} "
            f"({self.reason})"
        )


class UserSkillFlag(models.Model):
    """
    Per user-skill adaptive flags.
    A user can have multiple flags per skill (e.g. both 'struggling' and 'too_easy'
    are prevented by the unique_together constraint).
    """
    FLAG_CHOICES = [
        ('too_easy', 'Too Easy'),
        ('struggling', 'Struggling'),
        ('mastered', 'Mastered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_flags')
    skill = models.ForeignKey('skills.Skill', on_delete=models.CASCADE, related_name='user_flags')
    flag = models.CharField(max_length=20, choices=FLAG_CHOICES)
    reason = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('user', 'skill', 'flag')
        verbose_name = 'User Skill Flag'
        verbose_name_plural = 'User Skill Flags'
        indexes = [
            models.Index(fields=['user', 'flag'], name='userskillflag_user_flag_idx'),
            models.Index(fields=['skill', 'flag'], name='userskillflag_skill_flag_idx'),
        ]

    def __str__(self):
        return f"{self.user.username} — {self.skill.title}: {self.flag}"
