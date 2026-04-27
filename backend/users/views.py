from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from django.db.models import Sum
from django.db.models.functions import TruncDate
from django.utils import timezone
from datetime import timedelta
from .models import User, XPLog
from .serializers import DashboardSerializer, UserProfileSerializer
from quests.models import Quest
from skills.models import Skill, SkillProgress

class MeView(APIView):
    """
    Returns the authenticated user's profile.
    Called by the frontend after login/registration.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        user_rank = User.objects.filter(xp__gt=user.xp).count() + 1
        user.rank = user_rank
        serializer = UserProfileSerializer(user)
        return Response(serializer.data)


class DashboardView(APIView):
    """
    Combined endpoint for the user dashboard.
    Returns profile, XP history, active quests, leaderboard, and skill progress.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        
        # Calculate current rank
        user_rank = User.objects.filter(xp__gt=user.xp).count() + 1
        user.rank = user_rank # Temporary attribute for serializer or manual addition
        
        # 1. XP History (Last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        from django.db.models.functions import TruncDate
        history_data = XPLog.objects.filter(
            user=user,
            created_at__gte=seven_days_ago
        ).annotate(
            day=TruncDate('created_at')
        ).values('day').annotate(
            xp_gained=Sum('amount')
        ).order_by('day')
        
        xp_history = [
            {"date": str(item['day']), "xp_gained": item['xp_gained']}
            for item in history_data
        ]

        # 2. Active Quests
        # Get skills that are in progress for this user
        in_progress_skill_ids = SkillProgress.objects.filter(
            user=user, 
            status='in_progress'
        ).values_list('skill_id', flat=True)
        
        # Find quests in those skills that the user hasn't successfully completed
        active_quests = Quest.objects.filter(
            skill_id__in=in_progress_skill_ids
        ).exclude(
            submissions__user=user, 
            submissions__status='passed'
        ).distinct()[:5]

        # 3. Top Leaderboard
        top_users = User.objects.order_by('-xp')[:5]
        top_leaderboard = [
            {
                "username": u.username, 
                "xp": u.xp, 
                "level": u.level, 
                "avatar_url": u.avatar_url,
                "rank": i + 1
            } 
            for i, u in enumerate(top_users)
        ]

        # 4. Skills Progress
        total_skills = Skill.objects.count()
        completed_skills = SkillProgress.objects.filter(user=user, status='completed').count()
        in_progress_skills = SkillProgress.objects.filter(user=user, status='in_progress').count()
        
        skills_progress = {
            "total": total_skills,
            "completed": completed_skills,
            "in_progress": in_progress_skills
        }

        data = {
            "user": user,
            "xp_history": xp_history,
            "active_quests": active_quests,
            "top_leaderboard": top_leaderboard,
            "skills_progress": skills_progress
        }

        serializer = DashboardSerializer(data, context={'request': request})
        return Response(serializer.data)
