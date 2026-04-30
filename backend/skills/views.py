from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch, Avg, Count, Q
from django.shortcuts import get_object_or_404
import logging
from .models import Skill, SkillProgress, SkillPrerequisite, GeneratedSkillTree
from .serializers import (
    SkillSerializer, SkillProgressSerializer,
    GeneratedSkillTreeSerializer, GeneratedSkillTreeDetailSerializer
)
from quests.models import Quest

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

        # ── Batch-load all data to eliminate N+1 queries ──────────────────────
        # Force evaluation so we have a stable list of IDs.
        skills = list(skills)
        skill_ids = [s.id for s in skills]

        # 1 query: all SkillProgress rows for this user across all visible skills
        user_progress_map = {
            sp.skill_id: sp.status
            for sp in SkillProgress.objects.filter(
                user=request.user,
                skill_id__in=skill_ids
            )
        }

        # 1 query: all completed skill IDs for this user (used for prereq checks)
        completed_prereq_ids = set(
            SkillProgress.objects.filter(
                user=request.user,
                status='completed'
            ).values_list('skill_id', flat=True)
        )

        # 1 query: quest count per skill
        quest_counts = {
            row['skill_id']: row['count']
            for row in (
                Quest.objects.filter(skill_id__in=skill_ids)
                .values('skill_id')
                .annotate(count=Count('id'))
            )
        }
        # ─────────────────────────────────────────────────────────────────────

        nodes = []
        edges = []

        for skill in skills:
            # Determine user status from pre-fetched map (zero extra queries)
            if skill.id in user_progress_map:
                status_val = user_progress_map[skill.id]
            else:
                unmet_prereqs = any(
                    prereq.id not in completed_prereq_ids
                    for prereq in skill.prerequisites.all()  # uses prefetch cache
                )
                status_val = (
                    'available'
                    if not unmet_prereqs and request.user.xp >= skill.xp_required_to_unlock
                    else 'locked'
                )

            # Build prereq list from prefetch cache + completed set (zero extra queries)
            prereq_list = [
                {
                    "id": prereq.id,
                    "name": prereq.title,
                    "completed": prereq.id in completed_prereq_ids,
                }
                for prereq in skill.prerequisites.all()
            ]

            nodes.append({
                "id": skill.id,
                "name": skill.title,
                "description": skill.description,
                "category": CATEGORY_MAP.get(skill.category, skill.category),
                "difficulty": skill.difficulty,
                "status": status_val,
                "xpRequired": skill.xp_required_to_unlock,
                "prerequisites": prereq_list,
                "questCount": quest_counts.get(skill.id, 0),
            })

            # Create edges from prerequisites (uses prefetch cache)
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
        
        serializer = GeneratedSkillTreeDetailSerializer(tree, context={'request': request})
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
            # FIX: was calling non-existent method autofill_quests_for_tree;
            # the correct method is execute_autofill.
            result = service.execute_autofill(str(tree_id))

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



class SkillRadarView(APIView):
    """
    GET /api/skills/radar/
    Returns skill mastery data for 5 categories (Algorithms, Data Structures, Systems, Web Dev, AI/ML).
    Computes category_mastery as mean(mastery_score) across skills in each category.
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        try:
            # Define the 5 core categories
            CATEGORIES = {
                'algorithms': 'Algorithms',
                'ds': 'Data Structures',
                'systems': 'Systems',
                'webdev': 'Web Development',
                'aiml': 'AI/ML',
            }
            
            radar_data = []
            
            for category_key, category_name in CATEGORIES.items():
                # Get all skills in this category
                skills_in_category = Skill.objects.filter(category=category_key)
                
                # Get user's progress for skills in this category
                user_progress = SkillProgress.objects.filter(
                    user=request.user,
                    skill__in=skills_in_category
                )
                
                # Calculate mastery percentage
                if user_progress.exists():
                    # Count completed skills
                    completed = user_progress.filter(status='completed').count()
                    total = user_progress.count()
                    mastery_pct = int((completed / total) * 100) if total > 0 else 0
                    
                    # Get top skill in category
                    top_skill_progress = user_progress.filter(
                        status='completed'
                    ).first()
                    
                    top_skill = None
                    if top_skill_progress:
                        top_skill = {
                            'title': top_skill_progress.skill.title,
                            'mastery_tier': 'Mastered'
                        }
                else:
                    # No progress in this category
                    mastery_pct = 0
                    completed = 0
                    total = skills_in_category.count()
                    top_skill = None
                
                radar_data.append({
                    'category': category_name,
                    'category_key': category_key,
                    'mastery_pct': mastery_pct,
                    'skills_completed': completed,
                    'skills_total': total,
                    'top_skill': top_skill,
                })
            
            return Response({
                'data': radar_data,
                'timestamp': __import__('django.utils.timezone', fromlist=['now']).now().isoformat(),
            })
            
        except Exception as e:
            logger.error(f"Failed to compute skill radar: {str(e)}", exc_info=True)
            return Response(
                {"error": "Failed to compute skill radar"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
