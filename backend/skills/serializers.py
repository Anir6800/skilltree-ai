"""
Skills Serializers — SkillTree AI
===================================
Schema-aligned with the 2024 migration:
  - Skill gains tree_depth, created_at, updated_at
  - SkillProgress reflects the updated status lifecycle
  - GeneratedSkillTree exposes depth and status
  - SkillSerializer.get_status() is N+1-safe: reads context['progress_map']
    when injected by a view (batch loads); falls back to a single query only
    for single-object serialization (admin / DRF browsable API).
"""

from rest_framework import serializers
from .models import Skill, SkillProgress, GeneratedSkillTree, EmbeddingRecord


class SkillSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Skill nodes.

    N+1-safe status computation:
        Views that serialize many skills should inject a pre-built progress map
        into the serializer context:

            context = {
                'request': request,
                'progress_map': {skill_id: status_str, ...},
                'completed_ids': {skill_id, ...},
            }

        When these keys are absent the serializer falls back to individual DB
        queries (acceptable for single-object use, e.g., admin detail views).
    """
    status = serializers.SerializerMethodField()
    prerequisites_count = serializers.SerializerMethodField()

    class Meta:
        model = Skill
        fields = [
            'id', 'title', 'description', 'category', 'difficulty',
            'tree_depth', 'xp_required_to_unlock', 'status',
            'prerequisites_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_status(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return 'locked'

        # Fast path: view injected a pre-built progress map (batch load)
        progress_map = self.context.get('progress_map')
        if progress_map is not None:
            if obj.id in progress_map:
                return progress_map[obj.id]
            # Not in map → check unlock eligibility using completed_ids
            completed_ids = self.context.get('completed_ids', set())
            prereqs = list(obj.prerequisites.all())  # cached by prefetch_related
            unmet = any(p.id not in completed_ids for p in prereqs)
            if not unmet and user.xp >= obj.xp_required_to_unlock:
                return 'available'
            return 'locked'

        # Slow path: single-object serialization (admin / DRF browsable API)
        try:
            progress = SkillProgress.objects.get(user=user, skill=obj)
            return progress.status
        except SkillProgress.DoesNotExist:
            unmet = obj.prerequisites.exclude(
                user_progress__user=user,
                user_progress__status='completed'
            ).exists()
            if not unmet and user.xp >= obj.xp_required_to_unlock:
                return 'available'
            return 'locked'

    def get_prerequisites_count(self, obj):
        prereqs = list(obj.prerequisites.all())  # uses prefetch cache when available
        return len(prereqs)


class SkillProgressSerializer(serializers.ModelSerializer):
    """
    Serializer for tracking user's journey through a skill.
    Exposes denormalized counters for dashboard performance.
    """
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    skill_category = serializers.CharField(source='skill.category', read_only=True)
    skill_difficulty = serializers.IntegerField(source='skill.difficulty', read_only=True)

    class Meta:
        model = SkillProgress
        fields = [
            'id', 'skill', 'skill_title', 'skill_category', 'skill_difficulty',
            'status', 'completed_at',
            'quest_completion_count', 'attempts_count', 'time_spent_minutes',
            'updated_at',
        ]
        read_only_fields = [
            'id', 'completed_at', 'quest_completion_count',
            'attempts_count', 'time_spent_minutes', 'updated_at',
        ]


class GeneratedSkillTreeSerializer(serializers.ModelSerializer):
    """
    Serializer for AI-generated skill trees (list view).
    """
    skills_count = serializers.SerializerMethodField()
    stub_quests_remaining = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = GeneratedSkillTree
        fields = [
            'id', 'topic', 'created_by', 'created_by_username', 'is_public',
            'status', 'depth', 'skills_count', 'stub_quests_remaining',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'status', 'created_at', 'updated_at']

    def get_skills_count(self, obj):
        return obj.skills_created.count()

    def get_stub_quests_remaining(self, obj):
        """Count stub quests not yet filled — used by frontend to show autofill progress."""
        from quests.models import Quest
        return Quest.objects.filter(
            skill__in=obj.skills_created.all(),
            is_stub=True
        ).count()


class GeneratedSkillTreeDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for AI-generated skill trees with full skill data.
    Injects batch progress context into nested SkillSerializer instances.
    """
    skills = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)

    class Meta:
        model = GeneratedSkillTree
        fields = [
            'id', 'topic', 'created_by', 'created_by_username', 'is_public',
            'status', 'depth', 'skills', 'raw_ai_response', 'created_at', 'updated_at',
        ]
        read_only_fields = [
            'id', 'created_by', 'status', 'skills', 'raw_ai_response',
            'created_at', 'updated_at',
        ]

    def get_skills(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)

        skills = list(obj.skills_created.prefetch_related('prerequisites').all())

        # Build progress context for N+1-safe status resolution
        progress_map = {}
        completed_ids = set()
        if user and user.is_authenticated:
            skill_ids = [s.id for s in skills]
            for sp in SkillProgress.objects.filter(user=user, skill_id__in=skill_ids):
                progress_map[sp.skill_id] = sp.status
            completed_ids = set(
                SkillProgress.objects.filter(user=user, status='completed').values_list('skill_id', flat=True)
            )

        context = {
            'request': request,
            'progress_map': progress_map,
            'completed_ids': completed_ids,
        }
        return SkillSerializer(skills, many=True, context=context).data


class EmbeddingRecordSerializer(serializers.ModelSerializer):
    """
    Serializer for ChromaDB embedding records.
    Used by admin and embedding sync status endpoints.
    """
    is_stale = serializers.SerializerMethodField()

    class Meta:
        model = EmbeddingRecord
        fields = [
            'id', 'content_type', 'object_id', 'collection_name',
            'chroma_id', 'embedded_at', 'updated_at', 'checksum', 'is_stale',
        ]
        read_only_fields = ['id', 'embedded_at', 'updated_at']

    def get_is_stale(self, obj):
        """
        Returns True when a related Skill's updated_at is newer than the
        EmbeddingRecord's updated_at (i.e. content changed since last embed).
        """
        if obj.content_type == 'skill':
            from skills.models import Skill
            try:
                skill = Skill.objects.get(pk=obj.object_id)
                return skill.updated_at > obj.updated_at
            except Skill.DoesNotExist:
                return True  # orphaned record
        return False
