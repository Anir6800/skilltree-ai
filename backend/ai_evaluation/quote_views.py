"""
SkillTree AI - Quote Generator API Views
REST endpoints for generating motivational quotes.
"""

import logging
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404

from quests.models import QuestSubmission
from ai_evaluation.quote_generator import quote_generator

logger = logging.getLogger(__name__)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_result_quote(request, submission_id: int):
    """
    GET /api/ai-evaluation/quotes/{submission_id}/
    Generate or retrieve a motivational quote for a quest submission.

    Returns:
        {
            "quote": "string",
            "tone": "string",
            "cached": boolean
        }
    """
    try:
        submission = get_object_or_404(
            QuestSubmission,
            id=submission_id,
            user=request.user
        )

        # Generate quote
        quote = quote_generator.generate_result_quote(submission)

        return Response(
            {
                'quote': quote,
                'submission_id': submission.id,
                'status': submission.status,
            },
            status=status.HTTP_200_OK
        )

    except QuestSubmission.DoesNotExist:
        return Response(
            {'error': 'Submission not found or access denied'},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        logger.error(f"Failed to generate quote for submission {submission_id}: {e}")
        return Response(
            {'error': 'Failed to generate quote'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def check_quote_service(request):
    """
    GET /api/ai-evaluation/quotes/service/status/
    Check if quote generation service is available.

    Returns:
        {
            "available": boolean,
            "service": "lm_studio"
        }
    """
    available = quote_generator.is_available()

    return Response(
        {
            'available': available,
            'service': 'lm_studio',
        },
        status=status.HTTP_200_OK
    )
