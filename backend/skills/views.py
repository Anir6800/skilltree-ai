from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from django.db.models import Prefetch
from .models import Skill, SkillProgress, SkillPrerequisite
from .serializers import SkillSerializer, SkillProgressSerializer

class SkillTreeView(APIView):
    """
    Returns the Skill Tree as a DAG (nodes and edges) for React Flow.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        skills = Skill.objects.all().prefetch_related('prerequisites')
        
        # Grid layout settings
        CATEGORIES = ['algorithms', 'ds', 'systems', 'webdev', 'aiml']
        X_SPACING = 300
        Y_SPACING = 150
        
        nodes = []
        edges = []
        category_counts = {cat: 0 for cat in CATEGORIES}

        for skill in skills:
            # Determine position
            col = CATEGORIES.index(skill.category) if skill.category in CATEGORIES else 0
            row = category_counts[skill.category]
            category_counts[skill.category] += 1
            
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

            nodes.append({
                "id": str(skill.id),
                "type": "skillNode",
                "data": {
                    "title": skill.title,
                    "category": skill.category,
                    "difficulty": skill.difficulty,
                    "status": status_val,
                    "xp_required": skill.xp_required_to_unlock
                },
                "position": {"x": col * X_SPACING, "y": row * Y_SPACING}
            })

            # Create edges from prerequisites
            for prereq in skill.prerequisites.all():
                edges.append({
                    "id": f"e{prereq.id}-{skill.id}",
                    "source": str(prereq.id),
                    "target": str(skill.id),
                    "animated": status_val != 'locked'
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
