from django.db import models
from django.conf import settings

class Skill(models.Model):
    """
    Core Skill node in the SkillTree AI graph.
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
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    difficulty = models.IntegerField(default=1)  # 1-5
    prerequisites = models.ManyToManyField(
        'self', 
        symmetrical=False, 
        through='SkillPrerequisite', 
        related_name='unlocks'
    )
    xp_required_to_unlock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.title} ({self.category})"

class SkillPrerequisite(models.Model):
    """
    Explicit through model for skill prerequisites (DAG edges).
    """
    from_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='prerequisite_edges')
    to_skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='dependent_edges')

    class Meta:
        unique_together = ('from_skill', 'to_skill')

    def __str__(self):
        return f"{self.from_skill.title} -> {self.to_skill.title}"

class SkillProgress(models.Model):
    """
    Tracks a user's journey through a specific skill.
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

    class Meta:
        indexes = [
            models.Index(fields=['user', 'status']),
        ]
        unique_together = ('user', 'skill')

    def __str__(self):
        return f"{self.user.username} - {self.skill.title} ({self.status})"