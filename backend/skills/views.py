from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from django.shortcuts import get_object_or_404
import logging
from .models import Skill, SkillProgress, SkillPrerequisite, GeneratedSkillTree
from .serializers import (
    SkillSerializer, SkillProgressSerializer,
    GeneratedSkillTreeSerializer, GeneratedSkillTreeDetailSerializer
)

logger = logging.getLogger(__name__)

class SkillTreeView(APIView):
    """
    Returns the Skill Tree as a DAG (nodes and edges) for React Flow.
    Only includes:
    - Non-generated skills (always visible)
    - Skills from published generated trees (is_public=True)
    - Skills from user's own generated trees
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        from django.db.models import Q
        
        try:
            # Get published trees and user's own trees
            published_trees = GeneratedSkillTree.objects.filter(is_public=True)
            user_trees = GeneratedSkillTree.objects.filter(created_by=request.user)
            
            # Get IDs of skills from published/user trees
            published_skill_ids = set(
                Skill.objects.filter(
                    generated_from_trees__in=published_trees | user_trees
                ).values_list('id', flat=True)
            )
            
            # Include non-generated skills + published generated skills
            skills = Skill.objects.filter(
                Q(generated_from_trees__isnull=True) |  # Non-generated skills
                Q(id__in=published_skill_ids)  # Published generated skills
            ).prefetch_related('prerequisites').distinct()
        except Exception as e:
            # Fallback if GeneratedSkillTree table doesn't exist (migration not run)
            logger.warning(f"GeneratedSkillTree query failed: {str(e)}. Falling back to all skills.")
            skills = Skill.objects.all().prefetch_related('prerequisites')
        
        # Category mapping for frontend
        CATEGORY_MAP = {
            'algorithms': 'algorithms',
            'ds': 'data-structures',
            'systems': 'systems',
            'webdev': 'web-dev',
            'aiml': 'ai-ml',
        }
        
        nodes = []
        edges = []

        for skill in skills:
            # Get status for this user
            try:
                progress = SkillProgress.objects.get(user=request.user, skill=skill)
                status_val = progress.status
            except SkillProgress.DoesNotExist:
                # Basic check for availability
                unmet_prereqs = skill.prerequisites.exclude(
                    user_progress__user=request.user, 
                    user_progress__status='completed'
                ).exists()
                status_val = 'available' if not unmet_prereqs and request.user.xp >= skill.xp_required_to_unlock else 'locked'

            # Get prerequisites with completion status
            prereq_list = []
            for prereq in skill.prerequisites.all():
                try:
                    prereq_progress = SkillProgress.objects.get(user=request.user, skill=prereq)
                    prereq_completed = prereq_progress.status == 'completed'
                except SkillProgress.DoesNotExist:
                    prereq_completed = False
                
                prereq_list.append({
                    "id": prereq.id,
                    "name": prereq.title,
                    "completed": prereq_completed
                })

            # Count linked quests
            quest_count = skill.quests.count() if hasattr(skill, 'quests') else 0

            nodes.append({
                "id": skill.id,
                "name": skill.title,
                "description": skill.description,
                "category": CATEGORY_MAP.get(skill.category, skill.category),
                "difficulty": skill.difficulty,
                "status": status_val,
                "xpRequired": skill.xp_required_to_unlock,
                "prerequisites": prereq_list,
                "questCount": quest_count,
            })

            # Create edges from prerequisites
            for prereq in skill.prerequisites.all():
                edges.append({
                    "source": prereq.id,
                    "target": skill.id,
                })

        return Response({"nodes": nodes, "edges": edges})

class StartSkillView(APIView):
    """
    Validates and starts a skill (sets status to 'in_progress').
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, pk):
        try:
            skill = Skill.objects.get(pk=pk)
        except Skill.DoesNotExist:
            return Response({"error": "Skill not found"}, status=status.HTTP_404_NOT_FOUND)

        # 1. Check prerequisites
        incomplete_prereqs = skill.prerequisites.exclude(
            user_progress__user=request.user, 
            user_progress__status='completed'
        )
        if incomplete_prereqs.exists():
            prereq_names = ", ".join([p.title for p in incomplete_prereqs])
            return Response({
                "error": "Prerequisites not met",
                "message": f"Complete the following first: {prereq_names}"
            }, status=status.HTTP_403_FORBIDDEN)

        # 2. Check XP
        if request.user.xp < skill.xp_required_to_unlock:
            return Response({
                "error": "Insufficient XP",
                "message": f"You need {skill.xp_required_to_unlock} XP to unlock this skill."
            }, status=status.HTTP_403_FORBIDDEN)

        # 3. Create or Update Progress
        progress, created = SkillProgress.objects.get_or_create(
            user=request.user,
            skill=skill
        )
        if progress.status == 'locked' or progress.status == 'available':
            progress.status = 'in_progress'
            progress.save()

        return Response(SkillProgressSerializer(progress).data)


class GenerateSkillTreeView(APIView):
    """
    POST /api/skills/generate/
    Generate a new AI-powered skill tree for a topic.
    Returns immediately with tree_id and status="generating".
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        topic = request.data.get('topic', '').strip()
        depth = request.data.get('depth', 3)
        
        if not topic:
            return Response(
                {"error": "Topic is required"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            depth = int(depth)
        except (ValueError, TypeError):
            depth = 3
        
        try:
            from skills.ai_tree_generator import SkillTreeGeneratorService
            
            service = SkillTreeGeneratorService()
            result = service.generate_tree(topic, request.user, depth)
            
            return Response(result, status=status.HTTP_202_ACCEPTED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {"error": "Failed to generate tree"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GeneratedSkillTreeListView(APIView):
    """
    GET /api/skills/generated/
    List user's generated skill trees.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        trees = GeneratedSkillTree.objects.filter(
            created_by=request.user
        ).order_by('-created_at')
        
        serializer = GeneratedSkillTreeSerializer(trees, many=True)
        return Response(serializer.data)


class GeneratedSkillTreeDetailView(APIView):
    """
    GET /api/skills/generated/{tree_id}/
    Get full details of a generated skill tree.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, tree_id):
        tree = get_object_or_404(GeneratedSkillTree, id=tree_id)
        
        # Check ownership or public access
        if tree.created_by != request.user and not tree.is_public:
            return Response(
                {"error": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        serializer = GeneratedSkillTreeDetailSerializer(tree)
        return Response(serializer.data)


class PublishSkillTreeView(APIView):
    """
    POST /api/skills/generated/{tree_id}/publish/
    Publish a generated tree to all users (staff only).
    Merges skills into global tree.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tree_id):
        if not request.user.is_staff:
            return Response(
                {"error": "Only staff can publish trees"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        tree = get_object_or_404(GeneratedSkillTree, id=tree_id)
        
        if tree.status != "ready":
            return Response(
                {"error": "Tree must be in 'ready' status to publish"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        tree.is_public = True
        tree.save(update_fields=['is_public'])
        
        serializer = GeneratedSkillTreeSerializer(tree)
        return Response(serializer.data)


class AutoFillQuestsView(APIView):
    """
    POST /api/skills/generated/{tree_id}/autofill-quests/
    Auto-fill all stub quests for a generated skill tree.
    Runs async via Celery and broadcasts progress via WebSocket.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, tree_id):
        tree = get_object_or_404(GeneratedSkillTree, id=tree_id)
        
        # Check ownership
        if tree.created_by != request.user and not request.user.is_staff:
            return Response(
                {"error": "Not authorized"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        try:
            from skills.quest_autofill import QuestAutoFillService
            
            service = QuestAutoFillService()
            result = service.autofill_quests_for_tree(tree_id)
            
            return Response(result, status=status.HTTP_202_ACCEPTED)
            
        except ValueError as e:
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f"Failed to start quest auto-fill: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to start quest auto-fill"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
