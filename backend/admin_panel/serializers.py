from rest_framework import serializers
from skills.models import Skill, SkillPrerequisite
from quests.models import Quest
from .models import AdminContent, AssessmentQuestion


class SkillPrerequisiteSerializer(serializers.ModelSerializer):
    """Serializer for skill prerequisites."""
    prerequisite_id = serializers.IntegerField(source='from_skill.id', read_only=True)
    prerequisite_title = serializers.CharField(source='from_skill.title', read_only=True)
    
    class Meta:
        model = SkillPrerequisite
        fields = ['id', 'prerequisite_id', 'prerequisite_title']


class AdminSkillSerializer(serializers.ModelSerializer):
    """Admin serializer for skills with full CRUD capabilities."""
    prerequisites = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Skill.objects.all(),
        required=False
    )
    prerequisite_details = SkillPrerequisiteSerializer(
        source='dependent_edges',
        many=True,
        read_only=True
    )
    quests_count = serializers.SerializerMethodField()
    content_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Skill
        fields = [
            'id', 'title', 'description', 'category', 'difficulty',
            'xp_required_to_unlock', 'prerequisites', 'prerequisite_details',
            'quests_count', 'content_count'
        ]
    
    def get_quests_count(self, obj):
        return obj.quests.count()
    
    def get_content_count(self, obj):
        return obj.admin_content.filter(status='published').count()
    
    def create(self, validated_data):
        prerequisites = validated_data.pop('prerequisites', [])
        skill = Skill.objects.create(**validated_data)
        skill.prerequisites.set(prerequisites)
        return skill
    
    def update(self, instance, validated_data):
        prerequisites = validated_data.pop('prerequisites', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        if prerequisites is not None:
            instance.prerequisites.set(prerequisites)
        
        return instance


class AdminQuestSerializer(serializers.ModelSerializer):
    """Admin serializer for quests."""
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quest
        fields = [
            'id', 'skill', 'skill_title', 'type', 'title', 'description',
            'starter_code', 'test_cases', 'xp_reward', 'estimated_minutes',
            'difficulty_multiplier', 'questions_count'
        ]
    
    def get_questions_count(self, obj):
        return obj.assessment_questions.count()


class AdminContentSerializer(serializers.ModelSerializer):
    """Serializer for admin-created content."""
    skill_title = serializers.CharField(source='skill.title', read_only=True)
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = AdminContent
        fields = [
            'id', 'skill', 'skill_title', 'content_type', 'title', 'body',
            'code_example', 'language', 'status', 'ai_review_notes',
            'created_by', 'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_by', 'created_at', 'updated_at']


class AssessmentQuestionSerializer(serializers.ModelSerializer):
    """Serializer for assessment questions."""
    quest_title = serializers.CharField(source='quest.title', read_only=True)
    
    class Meta:
        model = AssessmentQuestion
        fields = [
            'id', 'quest', 'quest_title', 'question_type', 'prompt',
            'correct_answer', 'mcq_options', 'test_cases',
            'validation_criteria', 'points', 'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
