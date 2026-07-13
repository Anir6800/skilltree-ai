"""
SkillTree AI — MongoEngine document definitions
================================================
1:1 port of the Django ORM models to MongoEngine documents.

Relationship strategy (see migration report §4 Entity Relationship Mapping):
  - ForeignKey            -> ReferenceField (with reverse_delete_rule)
  - OneToOneField         -> ReferenceField(unique=True)
  - ManyToManyField       -> ListField(ReferenceField(...))            [bounded]
                             OR a dedicated "edge" Document             [unbounded / has attrs]
  - through models        -> kept as their own Document (they carry data)
  - JSONField             -> DictField / ListField
  - unique_together       -> meta['indexes'] entry with 'unique': True
  - auto_now_add          -> DateTimeField(default=utcnow)
  - auto_now              -> refreshed in save() via TimeStampedMixin
  - Django auto PK (int)  -> Mongo ObjectId  (legacy int kept in `legacy_id`)
  - UUID PK               -> UUIDField(primary_key=True)  (preserves API contract)

IMPORTANT ordering rule (MongoEngine specific):
    A ReferenceField with `reverse_delete_rule` resolves its target at CLASS
    DEFINITION time. Unlike Django's lazy string refs, the target document must
    already be defined. Therefore documents below are declared in strict
    DEPENDENCY ORDER and use direct class references (not string names),
    except 'self' references which MongoEngine resolves specially.

`legacy_id` fields exist ONLY to make the ETL idempotent and to let the
migration remap relational FKs. They can be dropped post-cutover.
"""

import uuid
from datetime import datetime, date

from mongoengine import (
    Document,
    fields,
    CASCADE,
    NULLIFY,
    PULL,
)
from django.contrib.auth.hashers import make_password, check_password


def _utcnow():
    return datetime.utcnow()


# ---------------------------------------------------------------------------
# Mixins
# ---------------------------------------------------------------------------

class TimeStampedMixin(object):
    """Refresh `updated_at` on every save (emulates Django auto_now)."""

    def save(self, *args, **kwargs):
        if hasattr(self, "updated_at"):
            self.updated_at = _utcnow()
        return super().save(*args, **kwargs)


# ===========================================================================
# 1. User  (foundational — referenced by almost everything)
# ===========================================================================

class User(Document):
    """
    Custom user (replaces users.User / AbstractUser).

    Auth handled by mongo/auth.py (PyJWT + Django password hashers). Django's
    auth tables (groups/permissions/contenttypes) are NOT used after cutover;
    role + is_staff/is_superuser drive authorization.

    Invariant preserved: level = (xp // 500) + 1, recomputed on every save.
    """
    ROLE_CHOICES = ("student", "admin", "moderator")

    legacy_id = fields.IntField(null=True)
    username = fields.StringField(required=True, unique=True, max_length=150)
    email = fields.EmailField(null=True)
    password = fields.StringField()  # Django-format password hash

    xp = fields.IntField(default=0)
    level = fields.IntField(default=1)
    streak_days = fields.IntField(default=0)
    last_active = fields.DateTimeField(null=True)
    role = fields.StringField(choices=ROLE_CHOICES, default="student", max_length=20)
    avatar_url = fields.StringField(default="", max_length=500)

    is_active = fields.BooleanField(default=True)
    is_staff = fields.BooleanField(default=False)
    is_superuser = fields.BooleanField(default=False)
    date_joined = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "users",
        "indexes": [
            {"fields": ["username"], "unique": True},
            "role",
            "legacy_id",
        ],
    }

    def set_password(self, raw_password):
        self.password = make_password(raw_password)

    def check_password(self, raw_password):
        return check_password(raw_password, self.password or "")

    @property
    def is_authenticated(self):
        return True

    @property
    def is_anonymous(self):
        return False

    @property
    def pk(self):
        return self.id

    def save(self, *args, **kwargs):
        self.xp = int(self.xp or 0)
        self.level = (self.xp // 500) + 1
        return super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} (Lvl {self.level})"


# ===========================================================================
# 2. Skill  +  3. SkillPrerequisite (DAG edges)
# ===========================================================================

class Skill(TimeStampedMixin, Document):
    legacy_id = fields.IntField(null=True)
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField()
    category = fields.StringField(max_length=50)
    difficulty = fields.IntField(default=1)
    tree_depth = fields.IntField(default=0)
    xp_required_to_unlock = fields.IntField(default=0)
    xp_reward = fields.IntField(default=100)
    estimated_minutes = fields.IntField(default=60)
    skills_gained = fields.ListField(default=list)
    courses = fields.ListField(default=list)
    free_resources = fields.ListField(default=list)
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)

    # Django M2M `prerequisites` (through SkillPrerequisite) is represented by
    # the SkillPrerequisite edge collection — NOT inlined here — to keep the DAG
    # queryable in both directions without unbounded arrays.

    meta = {
        "collection": "skills",
        "indexes": [
            {"fields": ["category", "difficulty"]},
            {"fields": ["tree_depth", "difficulty"]},
            "-created_at",
            "legacy_id",
        ],
    }

    def prerequisites(self):
        """Skills that must be completed before this one (incoming edges)."""
        edges = SkillPrerequisite.objects(to_skill=self).only("from_skill")
        return [e.from_skill for e in edges]

    def unlocks(self):
        """Skills this one unlocks (outgoing edges)."""
        edges = SkillPrerequisite.objects(from_skill=self).only("to_skill")
        return [e.to_skill for e in edges]


class SkillPrerequisite(Document):
    """DAG edge: completing from_skill is required before to_skill unlocks."""
    legacy_id = fields.IntField(null=True)
    from_skill = fields.ReferenceField(Skill, required=True, reverse_delete_rule=CASCADE)
    to_skill = fields.ReferenceField(Skill, required=True, reverse_delete_rule=CASCADE)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "skill_prerequisites",
        "indexes": [
            {"fields": ["from_skill", "to_skill"], "unique": True},
            "to_skill",
        ],
    }


# ===========================================================================
# 4. GeneratedSkillTree (UUID pk; refs User + Skill)
# ===========================================================================

class GeneratedSkillTree(TimeStampedMixin, Document):
    """UUID primary key preserved so the existing tree_id API contract is stable."""
    STATUS_CHOICES = ("generating", "ready", "failed")

    id = fields.UUIDField(primary_key=True, default=uuid.uuid4, binary=False)
    topic = fields.StringField(required=True, max_length=200)
    created_by = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    is_public = fields.BooleanField(default=False)
    raw_ai_response = fields.DictField(default=dict)
    status = fields.StringField(choices=STATUS_CHOICES, default="generating", max_length=20)
    depth = fields.IntField(default=3)
    total_nodes = fields.IntField(default=0)
    nodes_completed = fields.IntField(default=0)
    stage = fields.StringField(default="", max_length=100)
    error = fields.StringField(default="")
    outline = fields.DictField(default=dict)
    skills_created = fields.ListField(fields.ReferenceField(Skill, reverse_delete_rule=PULL))
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "generated_skill_trees",
        "ordering": ["-created_at"],
        "indexes": [
            {"fields": ["created_by", "status"]},
            {"fields": ["is_public", "status"]},
            "-created_at",
            "topic",
        ],
    }


# ===========================================================================
# 5. Quest  +  6. QuestSubmission
# ===========================================================================

class Quest(TimeStampedMixin, Document):
    TYPE_CHOICES = ("coding", "debugging", "mcq", "exercise", "challenge")

    legacy_id = fields.IntField(null=True)
    skill = fields.ReferenceField(Skill, required=True, reverse_delete_rule=CASCADE)
    type = fields.StringField(choices=TYPE_CHOICES, max_length=20)
    title = fields.StringField(required=True, max_length=200)
    description = fields.StringField()
    starter_code = fields.StringField(default="")
    test_cases = fields.ListField(default=list)
    xp_reward = fields.IntField(default=0)
    estimated_minutes = fields.IntField(default=15)
    difficulty_multiplier = fields.FloatField(default=1.0)
    is_stub = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "quests",
        "indexes": [
            {"fields": ["skill", "type", "is_stub"]},
            {"fields": ["is_stub", "skill"]},
            "-created_at",
            "legacy_id",
        ],
    }


class QuestSubmission(TimeStampedMixin, Document):
    STATUS_CHOICES = (
        "pending", "running", "passed", "failed", "flagged",
        "explanation_provided", "approved", "confirmed_ai",
    )
    LANGUAGE_CHOICES = ("python", "javascript", "cpp", "java", "go")

    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    quest = fields.ReferenceField(Quest, required=True, reverse_delete_rule=CASCADE)
    code = fields.StringField()
    language = fields.StringField(choices=LANGUAGE_CHOICES, max_length=20)
    status = fields.StringField(choices=STATUS_CHOICES, default="pending", max_length=30)
    execution_result = fields.DictField(default=dict)
    ai_feedback = fields.DictField(default=dict)
    ai_detection_score = fields.FloatField(default=0.0)
    explanation = fields.StringField(default="")
    celery_task_id = fields.StringField(null=True, max_length=255)
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "quest_submissions",
        "ordering": ["-created_at"],
        "indexes": [
            {"fields": ["user", "quest"]},
            {"fields": ["user", "status", "-created_at"]},
            "celery_task_id",
            "legacy_id",
        ],
    }


# ===========================================================================
# 7. Badge  +  8. UserBadge  +  9. XPLog  +  10. WeeklyReport
# ===========================================================================

class Badge(Document):
    RARITY_CHOICES = ("common", "rare", "epic", "legendary")

    legacy_id = fields.IntField(null=True)
    slug = fields.StringField(required=True, unique=True, max_length=100)
    name = fields.StringField(required=True, max_length=100)
    description = fields.StringField()
    icon_emoji = fields.StringField(max_length=10)
    rarity = fields.StringField(choices=RARITY_CHOICES, default="common", max_length=20)
    unlock_condition = fields.DictField(default=dict)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "badges",
        "ordering": ["rarity", "name"],
        "indexes": [{"fields": ["slug"], "unique": True}, "rarity"],
    }


class UserBadge(Document):
    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    badge = fields.ReferenceField(Badge, required=True, reverse_delete_rule=CASCADE)
    earned_at = fields.DateTimeField(default=_utcnow)
    seen = fields.BooleanField(default=False)

    meta = {
        "collection": "user_badges",
        "ordering": ["-earned_at"],
        "indexes": [
            {"fields": ["user", "badge"], "unique": True},
            {"fields": ["user", "seen"]},
            "badge",
        ],
    }


class XPLog(Document):
    """Append-only XP event log. Never update/delete."""
    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    amount = fields.IntField(required=True)
    source = fields.StringField(max_length=200)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "xp_logs",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["user", "-created_at"]}],
    }


class WeeklyReport(TimeStampedMixin, Document):
    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    week_number = fields.IntField(required=True)
    year = fields.IntField(default=lambda: date.today().year)
    pdf_path = fields.StringField(default="", max_length=500)
    data = fields.DictField(default=dict)
    narrative = fields.DictField(default=dict)
    generated_at = fields.DateTimeField(default=_utcnow)
    viewed_at = fields.DateTimeField(null=True)

    meta = {
        "collection": "weekly_reports",
        "ordering": ["-generated_at"],
        "indexes": [
            {"fields": ["user", "week_number", "year"], "unique": True},
            {"fields": ["user", "-generated_at"]},
            {"fields": ["week_number", "year"]},
        ],
    }


# ===========================================================================
# 11-14. Study Groups
# ===========================================================================

class StudyGroup(Document):
    legacy_id = fields.IntField(null=True)
    name = fields.StringField(required=True, max_length=100)
    invite_code = fields.StringField(required=True, unique=True, max_length=6)
    created_by = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    max_members = fields.IntField(default=6)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "study_groups",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["invite_code"], "unique": True}, "created_by"],
    }

    def get_member_count(self):
        return StudyGroupMembership.objects(group=self).count()

    def is_full(self):
        return self.get_member_count() >= self.max_members


class StudyGroupMembership(Document):
    """Through-model (kept as its own collection)."""
    ROLE_CHOICES = ("owner", "member")

    legacy_id = fields.IntField(null=True)
    group = fields.ReferenceField(StudyGroup, required=True, reverse_delete_rule=CASCADE)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    role = fields.StringField(choices=ROLE_CHOICES, default="member", max_length=20)
    joined_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "study_group_memberships",
        "ordering": ["-joined_at"],
        "indexes": [{"fields": ["group", "user"], "unique": True}, "user"],
    }


class StudyGroupMessage(Document):
    legacy_id = fields.IntField(null=True)
    group = fields.ReferenceField(StudyGroup, required=True, reverse_delete_rule=CASCADE)
    sender = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    text = fields.StringField(required=True)
    sent_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "study_group_messages",
        "ordering": ["sent_at"],
        "indexes": [{"fields": ["group", "sent_at"]}, "sender"],
    }


class StudyGroupGoal(Document):
    legacy_id = fields.IntField(null=True)
    group = fields.ReferenceField(StudyGroup, required=True, reverse_delete_rule=CASCADE)
    skill = fields.ReferenceField(Skill, required=True, reverse_delete_rule=CASCADE)
    target_date = fields.DateTimeField(required=True)
    completed = fields.BooleanField(default=False)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "study_group_goals",
        "ordering": ["target_date"],
        "indexes": [{"fields": ["group", "skill"], "unique": True}, "skill"],
    }


# ===========================================================================
# 15-18. Onboarding & Adaptive
# ===========================================================================

class OnboardingProfile(TimeStampedMixin, Document):
    GOAL_CHOICES = ("job_prep", "interview", "upskill", "passion")

    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, unique=True, reverse_delete_rule=CASCADE)
    primary_goal = fields.StringField(choices=GOAL_CHOICES, max_length=20)
    target_role = fields.StringField(max_length=200)
    experience_years = fields.IntField(default=0)
    category_levels = fields.DictField(default=dict)
    selected_interests = fields.ListField(default=list)
    weekly_hours = fields.IntField(default=5)
    completed_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)
    path_generated = fields.BooleanField(default=False)
    generation_started_at = fields.DateTimeField(null=True)
    generated_tree = fields.ReferenceField(GeneratedSkillTree, null=True, reverse_delete_rule=NULLIFY)
    generated_topic = fields.StringField(default="", max_length=200)

    meta = {
        "collection": "onboarding_profiles",
        "ordering": ["-completed_at"],
        "indexes": [
            {"fields": ["user"], "unique": True},
            {"fields": ["generated_tree", "path_generated"]},
        ],
    }


class AdaptiveProfile(Document):
    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, unique=True, reverse_delete_rule=CASCADE)
    ability_score = fields.FloatField(default=0.5)
    preferred_difficulty = fields.IntField(default=3)
    last_adjusted = fields.DateTimeField(default=_utcnow)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "adaptive_profiles",
        "indexes": ["ability_score", "preferred_difficulty"],
    }

    def save(self, *args, **kwargs):
        self.last_adjusted = _utcnow()
        return super().save(*args, **kwargs)


class AdaptiveAdjustmentLog(Document):
    legacy_id = fields.IntField(null=True)
    profile = fields.ReferenceField(AdaptiveProfile, required=True, reverse_delete_rule=CASCADE)
    ability_before = fields.FloatField(required=True)
    ability_after = fields.FloatField(required=True)
    difficulty_before = fields.IntField(required=True)
    difficulty_after = fields.IntField(required=True)
    reason = fields.StringField(max_length=200)
    quest = fields.ReferenceField(Quest, null=True, reverse_delete_rule=NULLIFY)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "adaptive_adjustment_logs",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["profile", "-created_at"]}, "quest"],
    }


class UserSkillFlag(TimeStampedMixin, Document):
    FLAG_CHOICES = ("too_easy", "struggling", "mastered")

    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    skill = fields.ReferenceField(Skill, required=True, reverse_delete_rule=CASCADE)
    flag = fields.StringField(choices=FLAG_CHOICES, max_length=20)
    reason = fields.StringField(default="")
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "user_skill_flags",
        "indexes": [
            {"fields": ["user", "skill", "flag"], "unique": True},
            {"fields": ["user", "flag"]},
            {"fields": ["skill", "flag"]},
        ],
    }


# ===========================================================================
# 19. SkillProgress  +  20. UserCurriculum  +  21. EmbeddingRecord
# ===========================================================================

class SkillProgress(TimeStampedMixin, Document):
    STATUS_CHOICES = ("locked", "available", "in_progress", "completed")

    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    skill = fields.ReferenceField(Skill, required=True, reverse_delete_rule=CASCADE)
    status = fields.StringField(choices=STATUS_CHOICES, default="locked", max_length=20)
    completed_at = fields.DateTimeField(null=True)
    quest_completion_count = fields.IntField(default=0)
    time_spent_minutes = fields.IntField(default=0)
    attempts_count = fields.IntField(default=0)
    updated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "skill_progress",
        "indexes": [
            {"fields": ["user", "skill"], "unique": True},
            {"fields": ["user", "status"]},
            {"fields": ["user", "completed_at"]},
        ],
    }


class UserCurriculum(TimeStampedMixin, Document):
    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, unique=True, reverse_delete_rule=CASCADE)
    weeks = fields.ListField(default=list)
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)
    target_completion_date = fields.DateTimeField(null=True)
    weekly_hours = fields.IntField(default=5)
    total_quests = fields.IntField(default=0)

    meta = {
        "collection": "user_curricula",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["user", "-created_at"]}],
    }


class EmbeddingRecord(TimeStampedMixin, Document):
    COLLECTION_CHOICES = ("skill_knowledge", "code_patterns", "ai_code_samples")

    legacy_id = fields.IntField(null=True)
    content_type = fields.StringField(max_length=50)
    object_id = fields.IntField()
    collection_name = fields.StringField(choices=COLLECTION_CHOICES, max_length=50)
    chroma_id = fields.StringField(max_length=200)
    embedded_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)
    checksum = fields.StringField(default="", max_length=64)

    meta = {
        "collection": "embedding_records",
        "indexes": [
            {"fields": ["content_type", "object_id", "collection_name"], "unique": True},
            {"fields": ["content_type", "object_id"]},
            {"fields": ["collection_name", "updated_at"]},
        ],
    }


# ===========================================================================
# 22. SharedSolution  +  23. SolutionComment
# ===========================================================================

class SharedSolution(Document):
    legacy_id = fields.IntField(null=True)
    submission = fields.ReferenceField(QuestSubmission, required=True, unique=True, reverse_delete_rule=CASCADE)
    shared_at = fields.DateTimeField(default=_utcnow)
    # M2M upvotes -> list of user refs. Watch item: migrate to a dedicated
    # collection if a solution can attract tens of thousands of upvotes.
    upvotes = fields.ListField(fields.ReferenceField(User, reverse_delete_rule=PULL))
    views_count = fields.IntField(default=0)
    is_anonymous = fields.BooleanField(default=False)

    meta = {
        "collection": "shared_solutions",
        "ordering": ["-shared_at"],
        "indexes": ["-shared_at", "submission"],
    }

    def get_upvote_count(self):
        return len(self.upvotes or [])


class SolutionComment(Document):
    legacy_id = fields.IntField(null=True)
    solution = fields.ReferenceField(SharedSolution, required=True, reverse_delete_rule=CASCADE)
    author = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    text = fields.StringField(max_length=1000)
    parent = fields.ReferenceField("self", null=True, reverse_delete_rule=CASCADE)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "solution_comments",
        "ordering": ["created_at"],
        "indexes": [{"fields": ["solution", "parent", "created_at"]}, "author"],
    }


# ===========================================================================
# 24. ExecutionTask  +  25/26 Evaluation  +  27 Detection
# ===========================================================================

class ExecutionTask(Document):
    STATUS_CHOICES = ("queued", "processing", "completed", "failed")

    legacy_id = fields.IntField(null=True)
    submission = fields.ReferenceField(QuestSubmission, required=True, reverse_delete_rule=CASCADE)
    task_id = fields.StringField(required=True, unique=True, max_length=100)
    status = fields.StringField(choices=STATUS_CHOICES, default="queued", max_length=20)
    worker_node = fields.StringField(default="", max_length=100)
    started_at = fields.DateTimeField(null=True)
    finished_at = fields.DateTimeField(null=True)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "execution_tasks",
        "indexes": [
            {"fields": ["task_id"], "unique": True},
            {"fields": ["submission", "status"]},
            {"fields": ["worker_node", "status"]},
            "-created_at",
        ],
    }


class EvaluationResult(Document):
    legacy_id = fields.IntField(null=True)
    submission = fields.ReferenceField(QuestSubmission, required=True, unique=True, reverse_delete_rule=CASCADE)
    score = fields.FloatField(default=0.0)
    summary = fields.StringField(default="")
    pros = fields.ListField(default=list)
    cons = fields.ListField(default=list)
    suggestions = fields.ListField(default=list)
    evaluated_at = fields.DateTimeField(default=_utcnow)

    meta = {"collection": "evaluation_results", "ordering": ["-evaluated_at"]}


class StyleReport(Document):
    legacy_id = fields.IntField(null=True)
    submission = fields.ReferenceField(QuestSubmission, required=True, unique=True, reverse_delete_rule=CASCADE)
    readability_score = fields.IntField(default=0)
    naming_quality = fields.StringField(default="")
    idiomatic_patterns = fields.StringField(default="")
    style_issues = fields.ListField(default=list)
    positive_patterns = fields.ListField(default=list)
    generated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "style_reports",
        "ordering": ["-generated_at"],
        "indexes": ["submission", "-generated_at"],
    }


class DetectionLog(Document):
    legacy_id = fields.IntField(null=True)
    submission = fields.ReferenceField(QuestSubmission, required=True, reverse_delete_rule=CASCADE)
    embedding_score = fields.FloatField(default=0.0)
    llm_score = fields.FloatField(default=0.0)
    heuristic_score = fields.FloatField(default=0.0)
    final_score = fields.FloatField(default=0.0)
    llm_reasoning = fields.DictField(default=dict)
    analyzed_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "detection_logs",
        "ordering": ["-analyzed_at"],
        "indexes": [
            {"fields": ["submission", "-analyzed_at"]},
            {"fields": ["final_score", "-analyzed_at"]},
        ],
    }


# ===========================================================================
# 28. Match  +  29. MatchParticipant  +  30. LeaderboardSnapshot
# ===========================================================================

class Match(Document):
    STATUS_CHOICES = ("waiting", "active", "finished")

    legacy_id = fields.IntField(null=True)
    quest = fields.ReferenceField(Quest, required=True, reverse_delete_rule=CASCADE)
    status = fields.StringField(choices=STATUS_CHOICES, default="waiting", max_length=20)
    winner = fields.ReferenceField(User, null=True, reverse_delete_rule=NULLIFY)
    created_at = fields.DateTimeField(default=_utcnow)
    started_at = fields.DateTimeField(null=True)
    ended_at = fields.DateTimeField(null=True)

    meta = {
        "collection": "matches",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["status", "quest"]}, "winner", "-created_at"],
    }

    def participants(self):
        return [p.user for p in MatchParticipant.objects(match=self).only("user")]


class MatchParticipant(Document):
    legacy_id = fields.IntField(null=True)
    match = fields.ReferenceField(Match, required=True, reverse_delete_rule=CASCADE)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    score = fields.IntField(default=0)
    joined_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "match_participants",
        "indexes": [
            {"fields": ["match", "user"], "unique": True},
            {"fields": ["user", "-joined_at"]},
            {"fields": ["match", "-score"]},
        ],
    }


class LeaderboardSnapshot(Document):
    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    total_xp = fields.IntField(required=True)
    rank = fields.IntField(required=True)
    streak_days = fields.IntField(required=True)
    snapshot_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "leaderboard_snapshots",
        "ordering": ["rank"],
        "indexes": [{"fields": ["user", "snapshot_at"]}, "-snapshot_at"],
    }


# ===========================================================================
# 31. AIInteraction  +  32. HintUsage
# ===========================================================================

class AIInteraction(Document):
    INTERACTION_TYPE_CHOICES = ("hint", "explanation", "path_suggestion")

    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    interaction_type = fields.StringField(choices=INTERACTION_TYPE_CHOICES, max_length=20)
    context_prompt = fields.StringField()
    response = fields.StringField()
    tokens_used = fields.IntField(default=0)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "ai_interactions",
        "ordering": ["-created_at"],
        "indexes": [
            {"fields": ["user", "interaction_type", "-created_at"]},
            {"fields": ["interaction_type", "created_at"]},
        ],
    }


class HintUsage(Document):
    HINT_LEVEL_CHOICES = (1, 2, 3)
    MAX_DAILY_HINTS = 5

    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    quest = fields.ReferenceField(Quest, required=True, reverse_delete_rule=CASCADE)
    hint_level = fields.IntField(choices=HINT_LEVEL_CHOICES)
    hint_text = fields.StringField()
    xp_penalty = fields.IntField(default=0)
    requested_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "hint_usages",
        "ordering": ["-requested_at"],
        "indexes": [
            {"fields": ["user", "quest", "requested_at"]},
            {"fields": ["user", "-requested_at"]},
        ],
    }


# ===========================================================================
# 33-35. Admin panel
# ===========================================================================

class AdminContent(TimeStampedMixin, Document):
    CONTENT_TYPE_CHOICES = ("lesson", "tip", "example", "reference")
    STATUS_CHOICES = ("draft", "ai_reviewed", "published")

    legacy_id = fields.IntField(null=True)
    skill = fields.ReferenceField(Skill, required=True, reverse_delete_rule=CASCADE)
    content_type = fields.StringField(choices=CONTENT_TYPE_CHOICES, max_length=20)
    title = fields.StringField(required=True, max_length=200)
    body = fields.StringField()
    code_example = fields.StringField(default="")
    language = fields.StringField(default="python", max_length=20)
    status = fields.StringField(choices=STATUS_CHOICES, default="draft", max_length=20)
    ai_review_notes = fields.StringField(default="")
    created_by = fields.ReferenceField(User, null=True, reverse_delete_rule=NULLIFY)
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "admin_content",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["skill", "status"]}, "status"],
    }


class AssessmentQuestion(TimeStampedMixin, Document):
    QUESTION_TYPE_CHOICES = ("code", "mcq", "open_ended")

    legacy_id = fields.IntField(null=True)
    quest = fields.ReferenceField(Quest, required=True, reverse_delete_rule=CASCADE)
    question_type = fields.StringField(choices=QUESTION_TYPE_CHOICES, max_length=20)
    prompt = fields.StringField()
    correct_answer = fields.StringField()
    mcq_options = fields.ListField(default=list)
    test_cases = fields.ListField(default=list)
    validation_criteria = fields.StringField(default="")
    language = fields.StringField(default="python", max_length=20)
    points = fields.IntField(default=10)
    created_at = fields.DateTimeField(default=_utcnow)
    updated_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "assessment_questions",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["quest", "question_type"]}],
    }


class AssessmentSubmission(Document):
    STATUS_CHOICES = ("pending", "evaluating", "evaluated", "error")

    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    question = fields.ReferenceField(AssessmentQuestion, required=True, reverse_delete_rule=CASCADE)
    answer = fields.StringField()
    submitted_at = fields.DateTimeField(default=_utcnow)
    evaluated_at = fields.DateTimeField(null=True)
    status = fields.StringField(choices=STATUS_CHOICES, default="pending", max_length=20)
    result = fields.DictField(default=dict)
    score = fields.FloatField(default=0.0)
    passed = fields.BooleanField(null=True)

    meta = {
        "collection": "assessment_submissions",
        "ordering": ["-submitted_at"],
        "indexes": [{"fields": ["user", "question"]}, "status", "-submitted_at"],
    }


# ===========================================================================
# 36. PasswordResetCode  +  37. BlacklistedToken (new)
# ===========================================================================

class PasswordResetCode(Document):
    legacy_id = fields.IntField(null=True)
    user = fields.ReferenceField(User, required=True, reverse_delete_rule=CASCADE)
    code_hash = fields.StringField(max_length=128)
    expires_at = fields.DateTimeField(required=True)
    used_at = fields.DateTimeField(null=True)
    created_at = fields.DateTimeField(default=_utcnow)

    meta = {
        "collection": "password_reset_codes",
        "ordering": ["-created_at"],
        "indexes": [{"fields": ["user", "-created_at"]}, "expires_at"],
    }

    @classmethod
    def create_for_user(cls, user, code, expires_at):
        return cls(user=user, code_hash=make_password(code), expires_at=expires_at).save()

    def matches(self, code):
        return check_password(code, self.code_hash)

    def is_active(self):
        return self.used_at is None and self.expires_at > _utcnow()

    def mark_used(self):
        self.used_at = _utcnow()
        self.save()


class BlacklistedToken(Document):
    """Revoked refresh-token JTIs (replaces rest_framework_simplejwt blacklist)."""
    jti = fields.StringField(required=True, unique=True, max_length=255)
    user_id = fields.StringField(null=True)   # stringified user id (informational)
    blacklisted_at = fields.DateTimeField(default=_utcnow)
    expires_at = fields.DateTimeField(null=True)

    meta = {
        "collection": "blacklisted_tokens",
        "indexes": [
            {"fields": ["jti"], "unique": True},
            # TTL index: Mongo auto-purges expired blacklist rows.
            {"fields": ["expires_at"], "expireAfterSeconds": 0},
        ],
    }


# Registry used by the ETL / bootstrap (legacy "app.Model" -> document)
DOCUMENT_REGISTRY = {
    "users.User": User,
    "users.XPLog": XPLog,
    "users.Badge": Badge,
    "users.UserBadge": UserBadge,
    "users.WeeklyReport": WeeklyReport,
    "users.StudyGroup": StudyGroup,
    "users.StudyGroupMembership": StudyGroupMembership,
    "users.StudyGroupMessage": StudyGroupMessage,
    "users.StudyGroupGoal": StudyGroupGoal,
    "users.OnboardingProfile": OnboardingProfile,
    "users.AdaptiveProfile": AdaptiveProfile,
    "users.AdaptiveAdjustmentLog": AdaptiveAdjustmentLog,
    "users.UserSkillFlag": UserSkillFlag,
    "skills.GeneratedSkillTree": GeneratedSkillTree,
    "skills.Skill": Skill,
    "skills.SkillPrerequisite": SkillPrerequisite,
    "skills.SkillProgress": SkillProgress,
    "skills.UserCurriculum": UserCurriculum,
    "skills.EmbeddingRecord": EmbeddingRecord,
    "quests.Quest": Quest,
    "quests.QuestSubmission": QuestSubmission,
    "quests.SharedSolution": SharedSolution,
    "quests.SolutionComment": SolutionComment,
    "executor.ExecutionTask": ExecutionTask,
    "ai_evaluation.EvaluationResult": EvaluationResult,
    "ai_evaluation.StyleReport": StyleReport,
    "ai_detection.DetectionLog": DetectionLog,
    "multiplayer.Match": Match,
    "multiplayer.MatchParticipant": MatchParticipant,
    "leaderboard.LeaderboardSnapshot": LeaderboardSnapshot,
    "mentor.AIInteraction": AIInteraction,
    "mentor.HintUsage": HintUsage,
    "admin_panel.AdminContent": AdminContent,
    "admin_panel.AssessmentQuestion": AssessmentQuestion,
    "admin_panel.AssessmentSubmission": AssessmentSubmission,
    "auth_app.PasswordResetCode": PasswordResetCode,
}
