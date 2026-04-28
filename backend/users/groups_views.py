"""
SkillTree AI - Study Group Views
API endpoints for study group management.
"""

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from django.shortcuts import get_object_or_404
from django.db.models import Sum, F, Q
from django.utils import timezone
from datetime import timedelta
import string
import random

from users.models import StudyGroup, StudyGroupMembership, StudyGroupMessage, StudyGroupGoal
from users.serializers import (
    StudyGroupDetailSerializer,
    StudyGroupListSerializer,
    StudyGroupMessageSerializer,
    StudyGroupGoalSerializer,
)
from skills.models import Skill, SkillProgress


def generate_invite_code():
    """Generate a unique 6-character invite code."""
    chars = string.ascii_uppercase + string.digits
    while True:
        code = ''.join(random.choices(chars, k=6))
        if not StudyGroup.objects.filter(invite_code=code).exists():
            return code


class CreateGroupView(APIView):
    """
    POST /api/groups/create/
    Create a new study group.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        name = request.data.get('name', '').strip()

        if not name:
            return Response(
                {'error': 'Group name is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if len(name) > 100:
            return Response(
                {'error': 'Group name must be 100 characters or less'},
                status=status.HTTP_400_BAD_REQUEST
            )

        invite_code = generate_invite_code()

        group = StudyGroup.objects.create(
            name=name,
            invite_code=invite_code,
            created_by=request.user
        )

        StudyGroupMembership.objects.create(
            group=group,
            user=request.user,
            role='owner'
        )

        serializer = StudyGroupDetailSerializer(group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class JoinGroupView(APIView):
    """
    POST /api/groups/join/
    Join a study group via invite code.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        invite_code = request.data.get('invite_code', '').strip().upper()

        if not invite_code:
            return Response(
                {'error': 'Invite code is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        group = get_object_or_404(StudyGroup, invite_code=invite_code)

        if group.is_full():
            return Response(
                {'error': 'Group is full (max 6 members)'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership, created = StudyGroupMembership.objects.get_or_create(
            group=group,
            user=request.user,
            defaults={'role': 'member'}
        )

        if not created:
            return Response(
                {'error': 'You are already a member of this group'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StudyGroupDetailSerializer(group)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MyGroupView(APIView):
    """
    GET /api/groups/my-group/
    Get the authenticated user's study group (if any).
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        membership = StudyGroupMembership.objects.filter(
            user=request.user
        ).select_related('group').first()

        if not membership:
            return Response(
                {'error': 'You are not in a study group'},
                status=status.HTTP_404_NOT_FOUND
            )

        group = membership.group
        serializer = StudyGroupDetailSerializer(group)
        return Response(serializer.data)


class GroupLeaderboardView(APIView):
    """
    GET /api/groups/{id}/leaderboard/
    Get group members ranked by XP earned this week.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)

        membership = StudyGroupMembership.objects.filter(
            group=group,
            user=request.user
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this group'},
                status=status.HTTP_403_FORBIDDEN
            )

        week_ago = timezone.now() - timedelta(days=7)

        from users.models import XPLog

        leaderboard = []
        for member in group.members.all():
            user = member.user
            xp_this_week = XPLog.objects.filter(
                user=user,
                created_at__gte=week_ago
            ).aggregate(total=Sum('amount'))['total'] or 0

            leaderboard.append({
                'user_id': user.id,
                'username': user.username,
                'avatar_url': user.avatar_url,
                'level': user.level,
                'xp_this_week': xp_this_week,
                'total_xp': user.xp,
                'role': member.role,
            })

        leaderboard.sort(key=lambda x: x['xp_this_week'], reverse=True)

        return Response({
            'group_id': group.id,
            'group_name': group.name,
            'leaderboard': leaderboard
        })


class GroupGoalsView(APIView):
    """
    GET /api/groups/{id}/goals/
    Get all goals for a group.

    POST /api/groups/{id}/goals/
    Create a new goal for the group.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)

        membership = StudyGroupMembership.objects.filter(
            group=group,
            user=request.user
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this group'},
                status=status.HTTP_403_FORBIDDEN
            )

        goals = group.goals.all()
        serializer = StudyGroupGoalSerializer(goals, many=True)
        return Response(serializer.data)

    def post(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)

        membership = StudyGroupMembership.objects.filter(
            group=group,
            user=request.user
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this group'},
                status=status.HTTP_403_FORBIDDEN
            )

        skill_id = request.data.get('skill_id')
        target_date = request.data.get('target_date')

        if not skill_id or not target_date:
            return Response(
                {'error': 'skill_id and target_date are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        skill = get_object_or_404(Skill, id=skill_id)

        goal, created = StudyGroupGoal.objects.get_or_create(
            group=group,
            skill=skill,
            defaults={'target_date': target_date}
        )

        if not created:
            return Response(
                {'error': 'Goal for this skill already exists'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = StudyGroupGoalSerializer(goal)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GroupMessagesView(APIView):
    """
    GET /api/groups/{id}/messages/
    Get recent messages from a group.
    """
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)

        membership = StudyGroupMembership.objects.filter(
            group=group,
            user=request.user
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this group'},
                status=status.HTTP_403_FORBIDDEN
            )

        limit = int(request.query_params.get('limit', 50))
        messages = group.messages.all().order_by('-sent_at')[:limit]
        messages = list(reversed(messages))

        serializer = StudyGroupMessageSerializer(messages, many=True)
        return Response(serializer.data)


class LeaveGroupView(APIView):
    """
    POST /api/groups/{id}/leave/
    Leave a study group.
    """
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, group_id):
        group = get_object_or_404(StudyGroup, id=group_id)

        membership = StudyGroupMembership.objects.filter(
            group=group,
            user=request.user
        ).first()

        if not membership:
            return Response(
                {'error': 'You are not a member of this group'},
                status=status.HTTP_403_FORBIDDEN
            )

        if membership.role == 'owner' and group.members.count() > 1:
            return Response(
                {'error': 'Owner cannot leave group with other members. Transfer ownership first.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        membership.delete()

        if group.members.count() == 0:
            group.delete()

        return Response({'message': 'Left group successfully'})
