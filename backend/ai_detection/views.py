"""
AI Detection Views and API Endpoints
Handles AI detection flagging, explanations, and admin review workflow.
"""

import asyncio
import logging
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q

from quests.models import QuestSubmission
from ai_detection.services import ai_detector
from ai_detection.models import DetectionLog
from users.models import XPLog

logger = logging.getLogger(__name__)


def detect_ai_code(submission_id):
    """
    Synchronous wrapper for AI detection.
    Runs the async detection pipeline and returns results.
    
    Args:
        submission_id: ID of QuestSubmission to analyze
        
    Returns:
        DetectionResult with scores and reasoning
    """
    try:
        submission = QuestSubmission.objects.get(id=submission_id)
        
        # Run async detection in event loop
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            result = loop.run_until_complete(ai_detector.detect(submission))
            return result
        finally:
            loop.close()
            
    except QuestSubmission.DoesNotExist:
        logger.error(f"Submission {submission_id} not found")
        return None
    except Exception as e:
        logger.error(f"AI detection failed for submission {submission_id}: {e}", exc_info=True)
        return None


class SubmissionExplanationView(APIView):
    """
    POST /api/ai-detection/submissions/{id}/explain/
    Authenticated owner only. Accept explanation for flagged submission.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, submission_id):
        submission = get_object_or_404(QuestSubmission, id=submission_id)
        
        # Ownership check
        if submission.user != request.user:
            return Response(
                {"error": "You can only explain your own submissions"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Only allow explanation if flagged
        if submission.status not in ['flagged', 'explanation_provided']:
            return Response(
                {"error": f"Cannot explain submission with status '{submission.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        explanation = request.data.get('explanation', '').strip()
        
        # Validate explanation length
        if len(explanation) < 200:
            return Response(
                {"error": "Explanation must be at least 200 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(explanation) > 5000:
            return Response(
                {"error": "Explanation cannot exceed 5000 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Update submission
        submission.explanation = explanation
        submission.status = 'explanation_provided'
        submission.save(update_fields=['explanation', 'status'])
        
        return Response({
            'id': submission.id,
            'status': submission.status,
            'explanation': submission.explanation,
            'ai_detection_score': submission.ai_detection_score,
        }, status=status.HTTP_200_OK)


class FlaggedSubmissionsView(APIView):
    """
    GET /api/ai-detection/admin/flagged-submissions/
    Admin only. List all flagged submissions with detection details.
    """
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        # Admin check
        if not request.user.is_staff:
            return Response(
                {"error": "Admin privileges required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Get all flagged submissions
        submissions = QuestSubmission.objects.filter(
            status__in=['flagged', 'explanation_provided']
        ).select_related('user', 'quest').order_by('-created_at')
        
        # Optional filtering
        status_filter = request.query_params.get('status')
        if status_filter in ['flagged', 'explanation_provided']:
            submissions = submissions.filter(status=status_filter)
        
        user_filter = request.query_params.get('user_id')
        if user_filter:
            submissions = submissions.filter(user_id=user_filter)
        
        # Get detection logs for each submission
        data = []
        for submission in submissions:
            detection_log = DetectionLog.objects.filter(
                submission=submission
            ).order_by('-analyzed_at').first()
            
            data.append({
                'id': submission.id,
                'user': {
                    'id': submission.user.id,
                    'username': submission.user.username,
                    'email': submission.user.email,
                },
                'quest': {
                    'id': submission.quest.id,
                    'title': submission.quest.title,
                },
                'status': submission.status,
                'code': submission.code[:500],  # First 500 chars for preview
                'code_full_length': len(submission.code),
                'language': submission.language,
                'ai_detection_score': submission.ai_detection_score,
                'explanation': submission.explanation,
                'created_at': submission.created_at.isoformat(),
                'detection_log': {
                    'embedding_score': detection_log.embedding_score if detection_log else 0.0,
                    'llm_score': detection_log.llm_score if detection_log else 0.0,
                    'heuristic_score': detection_log.heuristic_score if detection_log else 0.0,
                    'llm_reasoning': detection_log.llm_reasoning if detection_log else {},
                } if detection_log else None,
            })
        
        return Response({
            'count': len(data),
            'results': data,
        }, status=status.HTTP_200_OK)


class SubmissionReviewView(APIView):
    """
    POST /api/admin/submissions/{id}/review/
    Admin only. Review and approve/override flagged submission.
    """
    permission_classes = [IsAuthenticated]
    
    def post(self, request, submission_id):
        # Admin check
        if not request.user.is_staff:
            return Response(
                {"error": "Admin privileges required"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        submission = get_object_or_404(QuestSubmission, id=submission_id)
        
        # Only allow review if flagged or explanation provided
        if submission.status not in ['flagged', 'explanation_provided']:
            return Response(
                {"error": f"Cannot review submission with status '{submission.status}'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        action = request.data.get('action')
        admin_note = request.data.get('admin_note', '').strip()
        
        if action not in ['approve', 'override']:
            return Response(
                {"error": "Action must be 'approve' or 'override'"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if len(admin_note) > 1000:
            return Response(
                {"error": "Admin note cannot exceed 1000 characters"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        user = submission.user
        quest = submission.quest
        xp_earned = int(quest.xp_reward * quest.difficulty_multiplier)
        
        if action == 'approve':
            # Award XP retroactively if not already awarded
            already_awarded = XPLog.objects.filter(
                user=user,
                source__contains=f"Quest: {quest.title}"
            ).exists()
            
            if not already_awarded:
                user.xp += xp_earned
                user.save(update_fields=['xp', 'level'])
                
                XPLog.objects.create(
                    user=user,
                    amount=xp_earned,
                    source=f"Quest: {quest.title} (Admin approved)"
                )
            
            submission.status = 'approved'
            submission.save(update_fields=['status'])
            
            # Notify user via WebSocket
            try:
                from multiplayer.consumers import notify_user
                notify_user(user.id, {
                    'type': 'ai_detection_approved',
                    'submission_id': submission.id,
                    'message': 'Your explanation was approved! XP has been awarded.',
                    'xp_awarded': xp_earned,
                })
            except Exception as e:
                logger.warning(f"Failed to notify user {user.id}: {e}")
            
            return Response({
                'id': submission.id,
                'status': submission.status,
                'action': 'approved',
                'message': 'Submission approved. XP awarded retroactively.',
                'xp_awarded': xp_earned,
                'admin_note': admin_note,
            }, status=status.HTTP_200_OK)
        
        elif action == 'override':
            # Revoke XP, mark as confirmed AI
            if user.xp >= xp_earned:
                user.xp -= xp_earned
                user.save(update_fields=['xp', 'level'])
                
                XPLog.objects.create(
                    user=user,
                    amount=-xp_earned,
                    source=f"AI Cheating Detected: {quest.title} (Admin override)"
                )
            
            submission.status = 'confirmed_ai'
            submission.save(update_fields=['status'])
            
            # Notify user via WebSocket
            try:
                from multiplayer.consumers import notify_user
                notify_user(user.id, {
                    'type': 'ai_detection_rejected',
                    'submission_id': submission.id,
                    'message': 'Your submission was confirmed as AI-generated. XP has been revoked.',
                    'xp_revoked': xp_earned,
                })
            except Exception as e:
                logger.warning(f"Failed to notify user {user.id}: {e}")
            
            return Response({
                'id': submission.id,
                'status': submission.status,
                'action': 'overridden',
                'message': f'Submission marked as AI-generated. {xp_earned} XP revoked.',
                'xp_revoked': xp_earned,
                'admin_note': admin_note,
            }, status=status.HTTP_200_OK)
