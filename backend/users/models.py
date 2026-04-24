from django.contrib.auth.models import AbstractUser
from django.db import models

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
