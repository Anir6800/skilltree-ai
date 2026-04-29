"""
Quest Views - UPDATED
Includes skill lock enforcement and breadcrumb navigation.
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from quests.models import Quest, QuestSubmission
from skills.models import SkillProgress
from quests.serializers import QuestSerializer, QuestSubmissionSerializer
from executor.tasks import evaluate_submission

logger = logging.getLogger(__name__)


class QuestDetailView(APIView):
    """
    Get quest details with breadcrumb navigation.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, quest_id):
        """
        Get quest details including breadcrumb data.
        
        Args:
            request: HTTP request
            quest_id: Quest ID
            
        Returns:
            Quest details with breadcrumb
        """
        try:
            quest = get_object_or_404(Quest, id=quest_id)
            skill = quest.skill
            
            # NEW: Build breadcrumb data
            breadcrumb = {
                'skill': {
                    'id': skill.id,
                    'title': skill.title,
                    'category': skill.category,
                },
                'quest': {
                    'id': quest.id,
                    'title': quest.title,
                    'type': quest.type,
                }
            }
            
            serializer = QuestSerializer(quest)
            
            return Response({
                'quest': serializer.data,
                'breadcrumb': breadcrumb,  # NEW: Include breadcrumb
            })
        
        except Exception as e:
            logger.error(f"Failed to get quest {quest_id}: {str(e)}")
            return Response(
                {'error': 'Failed to load quest'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuestSubmitView(APIView):
    """
    Submit quest solution with skill lock enforcement.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, quest_id):
        """
        Submit quest solution.
        
        Args:
            request: HTTP request with code, language
            quest_id: Quest ID
            
        Returns:
            Submission created response
        """
        try:
            quest = get_object_or_404(Quest, id=quest_id)
            user = request.user
            
            # NEW: Check skill status
            logger.info(f"[SUBMIT] Checking skill status for user {user.id}, skill {quest.skill.id}")
            
            try:
                skill_progress = SkillProgress.objects.get(user=user, skill=quest.skill)
            except SkillProgress.DoesNotExist:
                logger.warning(f"[SUBMIT] No skill progress found for user {user.id}, skill {quest.skill.id}")
                return Response(
                    {'error': 'Skill not started. Please start the skill first.'},
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # NEW: Enforce skill lock
            if skill_progress.status == 'locked':
                logger.warning(f"[SUBMIT] Skill locked for user {user.id}, skill {quest.skill.id}")
                return Response(
                    {
                        'error': 'Skill is locked. Complete prerequisites first.',
                        'prerequisites': self._get_prerequisites_info(quest.skill)
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Validate request data
            code = request.data.get('code', '').strip()
            language = request.data.get('language', '').lower()
            
            if not code:
                return Response(
                    {'error': 'Code cannot be empty'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if language not in ['python', 'javascript', 'cpp', 'java', 'go']:
                return Response(
                    {'error': f'Unsupported language: {language}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # NEW: Check code length
            MAX_CODE_LENGTH = getattr(settings, 'EXECUTOR_MAX_CODE_LENGTH', 50000)
            if len(code) > MAX_CODE_LENGTH:
                return Response(
                    {'error': f'Code exceeds maximum length of {MAX_CODE_LENGTH} characters'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Create submission
            logger.info(f"[SUBMIT] Creating submission for user {user.id}, quest {quest_id}")
            
            submission = QuestSubmission.objects.create(
                user=user,
                quest=quest,
                code=code,
                language=language,
                status='pending',
            )
            
            # Dispatch evaluation task
            logger.info(f"[SUBMIT] Dispatching evaluation task for submission {submission.id}")
            evaluate_submission.delay(submission.id)
            
            # Update skill progress
            if skill_progress.status == 'available':
                skill_progress.status = 'in_progress'
                skill_progress.save(update_fields=['status'])
                logger.info(f"[SUBMIT] Updated skill progress to in_progress")
            
            # NEW: Increment attempts count
            skill_progress.attempts_count += 1
            skill_progress.save(update_fields=['attempts_count'])
            
            serializer = QuestSubmissionSerializer(submission)
            
            return Response(
                serializer.data,
                status=status.HTTP_201_CREATED
            )
        
        except Exception as e:
            logger.error(f"[SUBMIT] Failed to submit quest: {str(e)}", exc_info=True)
            return Response(
                {'error': 'Failed to submit quest'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_prerequisites_info(self, skill):
        """
        Get information about skill prerequisites.
        
        Args:
            skill: Skill object
            
        Returns:
            List of prerequisite skills
        """
        prerequisites = skill.prerequisites.all()
        return [
            {
                'id': prereq.id,
                'title': prereq.title,
                'category': prereq.category,
            }
            for prereq in prerequisites
        ]


class QuestListView(APIView):
    """
    List quests with filtering and skill lock status.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        """
        List quests with optional filtering.
        
        Args:
            request: HTTP request with optional query params
            
        Returns:
            List of quests
        """
        try:
            user = request.user
            
            # Get filter parameters
            skill_id = request.query_params.get('skill_id')
            quest_type = request.query_params.get('type')
            difficulty = request.query_params.get('difficulty')
            
            # Build query
            quests = Quest.objects.all()
            
            if skill_id:
                quests = quests.filter(skill_id=skill_id)
            
            if quest_type:
                quests = quests.filter(type=quest_type)
            
            if difficulty:
                try:
                    difficulty = int(difficulty)
                    quests = quests.filter(skill__difficulty=difficulty)
                except ValueError:
                    pass
            
            # Add user submission status
            quests = quests.select_related('skill')
            
            # Serialize with submission status
            quest_data = []
            for quest in quests:
                serializer = QuestSerializer(quest)
                quest_dict = serializer.data
                
                # Add submission status
                submission = QuestSubmission.objects.filter(
                    user=user,
                    quest=quest
                ).order_by('-created_at').first()
                
                quest_dict['user_status'] = submission.status if submission else 'not_started'
                
                # NEW: Add skill lock status
                try:
                    skill_progress = SkillProgress.objects.get(user=user, skill=quest.skill)
                    quest_dict['skill_locked'] = skill_progress.status == 'locked'
                except SkillProgress.DoesNotExist:
                    quest_dict['skill_locked'] = True
                
                quest_data.append(quest_dict)
            
            return Response(quest_data)
        
        except Exception as e:
            logger.error(f"Failed to list quests: {str(e)}")
            return Response(
                {'error': 'Failed to load quests'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class QuestSubmissionHistoryView(APIView):
    """
    Get user's submission history for a quest.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request, quest_id):
        """
        Get submission history for a quest.
        
        Args:
            request: HTTP request
            quest_id: Quest ID
            
        Returns:
            List of submissions
        """
        try:
            user = request.user
            quest = get_object_or_404(Quest, id=quest_id)
            
            submissions = QuestSubmission.objects.filter(
                user=user,
                quest=quest
            ).order_by('-created_at')
            
            serializer = QuestSubmissionSerializer(submissions, many=True)
            
            return Response(serializer.data)
        
        except Exception as e:
            logger.error(f"Failed to get submission history: {str(e)}")
            return Response(
                {'error': 'Failed to load submission history'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
