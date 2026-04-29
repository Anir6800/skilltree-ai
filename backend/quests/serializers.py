from rest_framework import serializers
from .models import Quest, QuestSubmission, SharedSolution, SolutionComment

class QuestListSerializer(serializers.ModelSerializer):
    """
    Brief serializer for listing quests.
    """
    status = serializers.SerializerMethodField()
    skill_name = serializers.CharField(source='skill.title', read_only=True)
    skill_id = serializers.IntegerField(source='skill.id', read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'type', 'description', 'xp_reward', 
            'difficulty_multiplier', 'estimated_minutes', 'status', 'skill_name', 'skill_id'
        ]

    def get_status(self, obj):
        request = self.context.get('request')
        if not request:
            return 'not_started'
            
        user = request.user
        if not user or not user.is_authenticated:
            return 'not_started'
        
        # Check for passed submission first
        passed_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status='passed'
        ).first()
        
        if passed_submission:
            return 'passed'
        
        # Check for in-progress submission
        in_progress_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status__in=['pending', 'running']
        ).first()
        
        if in_progress_submission:
            return 'in_progress'
        
        return 'not_started'

class QuestDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a single quest.
    Hides expected output from test cases for security.
    """
    status = serializers.SerializerMethodField()
    test_cases = serializers.SerializerMethodField()
    is_locked = serializers.SerializerMethodField()
    skill_name = serializers.CharField(source='skill.title', read_only=True)
    skill_id = serializers.IntegerField(source='skill.id', read_only=True)

    class Meta:
        model = Quest
        fields = [
            'id', 'title', 'description', 'type', 'starter_code', 
            'test_cases', 'xp_reward', 'difficulty_multiplier', 
            'estimated_minutes', 'status', 'skill_name', 'skill_id', 'is_locked'
        ]

    def get_is_locked(self, obj):
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return True
            
        user = request.user
        from skills.models import SkillProgress
        try:
            progress = SkillProgress.objects.get(user=user, skill=obj.skill)
            return progress.status == 'locked'
        except SkillProgress.DoesNotExist:
            unmet_prereqs = obj.skill.prerequisites.exclude(
                user_progress__user=user,
                user_progress__status='completed',
            ).exists()
            return unmet_prereqs or user.xp < obj.skill.xp_required_to_unlock

    def get_status(self, obj):
        request = self.context.get('request')
        if not request:
            return 'not_started'
            
        user = request.user
        if not user or not user.is_authenticated:
            return 'not_started'
        
        # Check for passed submission first
        passed_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status='passed'
        ).first()
        
        if passed_submission:
            return 'passed'
        
        # Check for in-progress submission
        in_progress_submission = QuestSubmission.objects.filter(
            user=user, 
            quest=obj, 
            status__in=['pending', 'running']
        ).first()
        
        if in_progress_submission:
            return 'in_progress'
        
        return 'not_started'

    def get_test_cases(self, obj):
        # Remove 'expected_output' to prevent cheating
        return [{"input": tc.get("input")} for tc in obj.test_cases]

class QuestSubmissionSerializer(serializers.ModelSerializer):
    """
    Serializer for quest attempts.
    """
    quest_title = serializers.CharField(source='quest.title', read_only=True)
    
    class Meta:
        model = QuestSubmission
        fields = [
            'id', 'quest', 'quest_title', 'code', 'language', 
            'status', 'execution_result', 'ai_feedback', 
            'ai_detection_score', 'created_at'
        ]
        read_only_fields = [
            'id', 'status', 'execution_result', 'ai_feedback', 
            'ai_detection_score', 'created_at'
        ]


class SolutionCommentSerializer(serializers.ModelSerializer):
    """
    Serializer for solution comments with author details.
    """
    author_username = serializers.CharField(source='author.username', read_only=True)
    author_avatar = serializers.CharField(source='author.avatar_url', read_only=True)
    author_level = serializers.IntegerField(source='author.level', read_only=True)
    replies = serializers.SerializerMethodField()

    class Meta:
        model = SolutionComment
        fields = [
            'id', 'author_username', 'author_avatar', 'author_level',
            'text', 'created_at', 'parent', 'replies'
        ]
        read_only_fields = ['id', 'author_username', 'author_avatar', 'author_level', 'created_at']

    def get_replies(self, obj):
        """Get nested replies."""
        if obj.replies.exists():
            return SolutionCommentSerializer(obj.replies.all(), many=True).data
        return []


class SharedSolutionDetailSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for a shared solution with code and comments.
    """
    user_username = serializers.CharField(source='submission.user.username', read_only=True)
    user_avatar = serializers.CharField(source='submission.user.avatar_url', read_only=True)
    user_level = serializers.IntegerField(source='submission.user.level', read_only=True)
    quest_title = serializers.CharField(source='submission.quest.title', read_only=True)
    quest_id = serializers.IntegerField(source='submission.quest.id', read_only=True)
    code = serializers.CharField(source='submission.code', read_only=True)
    language = serializers.CharField(source='submission.language', read_only=True)
    upvote_count = serializers.SerializerMethodField()
    user_upvoted = serializers.SerializerMethodField()
    comments = SolutionCommentSerializer(many=True, read_only=True)
    solve_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = SharedSolution
        fields = [
            'id', 'user_username', 'user_avatar', 'user_level',
            'quest_title', 'quest_id', 'code', 'language',
            'upvote_count', 'user_upvoted', 'views_count',
            'is_anonymous', 'shared_at', 'comments', 'solve_time_minutes'
        ]
        read_only_fields = [
            'id', 'user_username', 'user_avatar', 'user_level',
            'quest_title', 'quest_id', 'code', 'language',
            'upvote_count', 'views_count', 'shared_at'
        ]

    def get_upvote_count(self, obj):
        """Get total upvotes."""
        return obj.get_upvote_count()

    def get_user_upvoted(self, obj):
        """Check if current user upvoted."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.upvotes.filter(id=request.user.id).exists()

    def get_solve_time_minutes(self, obj):
        """Calculate solve time in minutes."""
        if obj.submission.created_at:
            time_diff = obj.shared_at - obj.submission.created_at
            return int(time_diff.total_seconds() / 60)
        return 0


class SharedSolutionListSerializer(serializers.ModelSerializer):
    """
    List serializer for shared solutions (brief).
    """
    user_username = serializers.CharField(source='submission.user.username', read_only=True)
    user_avatar = serializers.CharField(source='submission.user.avatar_url', read_only=True)
    user_level = serializers.IntegerField(source='submission.user.level', read_only=True)
    quest_title = serializers.CharField(source='submission.quest.title', read_only=True)
    language = serializers.CharField(source='submission.language', read_only=True)
    code_line_count = serializers.SerializerMethodField()
    upvote_count = serializers.SerializerMethodField()
    user_upvoted = serializers.SerializerMethodField()
    comment_count = serializers.SerializerMethodField()
    solve_time_minutes = serializers.SerializerMethodField()

    class Meta:
        model = SharedSolution
        fields = [
            'id', 'user_username', 'user_avatar', 'user_level',
            'quest_title', 'language', 'code_line_count',
            'upvote_count', 'user_upvoted', 'views_count',
            'comment_count', 'is_anonymous', 'shared_at', 'solve_time_minutes'
        ]
        read_only_fields = [
            'id', 'user_username', 'user_avatar', 'user_level',
            'quest_title', 'language', 'code_line_count',
            'upvote_count', 'views_count', 'comment_count', 'shared_at'
        ]

    def get_code_line_count(self, obj):
        """Count lines of code."""
        return len(obj.submission.code.split('\n'))

    def get_upvote_count(self, obj):
        """Get total upvotes."""
        return obj.get_upvote_count()

    def get_user_upvoted(self, obj):
        """Check if current user upvoted."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        return obj.upvotes.filter(id=request.user.id).exists()

    def get_comment_count(self, obj):
        """Get total comments (including replies)."""
        return obj.comments.count()

    def get_solve_time_minutes(self, obj):
        """Calculate solve time in minutes."""
        if obj.submission.created_at:
            time_diff = obj.shared_at - obj.submission.created_at
            return int(time_diff.total_seconds() / 60)
        return 0
