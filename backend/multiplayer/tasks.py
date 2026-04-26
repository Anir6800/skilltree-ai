import logging
from celery import shared_task
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from multiplayer.models import Match

logger = logging.getLogger(__name__)


@shared_task
def broadcast_submission_result(match_id, user_id, username, tests_passed, tests_total, is_winner):
    """
    Celery task to broadcast submission results to match participants.
    Called from executor service after code execution completes.
    
    Args:
        match_id: The match ID
        user_id: User who submitted
        username: Username for display
        tests_passed: Number of tests passed
        tests_total: Total number of tests
        is_winner: Whether this submission won the match
    """
    try:
        channel_layer = get_channel_layer()
        room_group_name = f'match_{match_id}'
        
        message = {
            'type': 'match_message',
            'message': {
                'type': 'submission_result',
                'user_id': user_id,
                'username': username,
                'tests_passed': tests_passed,
                'tests_total': tests_total,
                'is_winner': is_winner
            }
        }
        
        async_to_sync(channel_layer.group_send)(room_group_name, message)
        logger.info(f"Broadcast submission result for match {match_id}, user {username}")
        
    except Exception as e:
        logger.error(f"Failed to broadcast submission result: {str(e)}", exc_info=True)


@shared_task
def check_match_timeout(match_id, timeout_minutes=30):
    """
    Check if a match has timed out and finish it.
    Can be scheduled to run periodically.
    
    Args:
        match_id: The match ID to check
        timeout_minutes: Maximum duration in minutes
    """
    try:
        from django.utils import timezone
        from datetime import timedelta
        
        match = Match.objects.get(id=match_id)
        
        if match.status == 'active' and match.started_at:
            elapsed = timezone.now() - match.started_at
            if elapsed > timedelta(minutes=timeout_minutes):
                # Find participant with highest score
                best_participant = match.matchparticipant_set.order_by('-score').first()
                
                if best_participant:
                    match.winner = best_participant.user
                
                match.status = 'finished'
                match.ended_at = timezone.now()
                match.save()
                
                # Broadcast timeout
                channel_layer = get_channel_layer()
                room_group_name = f'match_{match_id}'
                
                message = {
                    'type': 'match_message',
                    'message': {
                        'type': 'match_timeout',
                        'winner': {
                            'id': match.winner.id,
                            'username': match.winner.username
                        } if match.winner else None
                    }
                }
                
                async_to_sync(channel_layer.group_send)(room_group_name, message)
                logger.info(f"Match {match_id} timed out after {timeout_minutes} minutes")
                
    except Match.DoesNotExist:
        logger.warning(f"Match {match_id} not found for timeout check")
    except Exception as e:
        logger.error(f"Failed to check match timeout: {str(e)}", exc_info=True)
