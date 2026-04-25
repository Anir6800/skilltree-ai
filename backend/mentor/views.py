"""
AI Mentor Views
Chat interface and learning path suggestions with RAG context.
"""

import json
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.db.models import Count, Q

from .models import AIInteraction
from .serializers import (
    ChatRequestSerializer,
    ChatResponseSerializer,
    PathSuggestionResponseSerializer,
    AIInteractionSerializer
)
from core.chroma_client import chroma_client
from core.lm_client import lm_client, ExecutionServiceUnavailable
from skills.models import Skill, SkillProgress
from quests.models import Quest, QuestSubmission


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def chat(request):
    """
    AI Mentor chat endpoint with RAG context.
    
    POST /api/mentor/chat/
    Body: {
        "message": "How do I optimize this algorithm?",
        "context_skill_id": 5,  # optional
        "context_quest_id": 12  # optional
    }
    
    Returns: {
        "response": "AI mentor response...",
        "tokens_used": 450,
        "interaction_id": 123
    }
    """
    serializer = ChatRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    user = request.user
    message = serializer.validated_data['message']
    context_skill_id = serializer.validated_data.get('context_skill_id')
    context_quest_id = serializer.validated_data.get('context_quest_id')
    
    try:
        # Build RAG context
        rag_context = _build_rag_context(context_skill_id, context_quest_id)
        
        # Build user history
        user_history = _build_user_history(user)
        
        # Construct system prompt
        system_prompt = f"""You are SkillTree's AI Mentor - a supportive, encouraging guide for developers learning to code.

Your role:
- Guide learners through their coding journey
- Provide clear, actionable advice
- Encourage growth mindset and persistence
- Suggest next steps based on their progress
- Be warm, friendly, and motivating

Current context:
{rag_context}

User's recent activity:
{user_history}

Guidelines:
- Keep responses concise (2-3 paragraphs max)
- Use encouraging language
- Provide specific, actionable suggestions
- Reference their progress when relevant
- Suggest related skills or quests when appropriate
- Use emojis sparingly for warmth (1-2 per response)"""
        
        # Call LM Studio
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": message}
        ]
        
        response = lm_client.chat_completion(
            messages=messages,
            max_tokens=800,
            temperature=0.7
        )
        
        response_text = lm_client.extract_content(response)
        tokens_used = response.get('usage', {}).get('total_tokens', 0)
        
        # Store interaction
        interaction = AIInteraction.objects.create(
            user=user,
            interaction_type='explanation',
            context_prompt=message,
            response=response_text,
            tokens_used=tokens_used
        )
        
        return Response({
            'response': response_text,
            'tokens_used': tokens_used,
            'interaction_id': interaction.id
        }, status=status.HTTP_200_OK)
        
    except ExecutionServiceUnavailable as e:
        return Response({
            'error': 'AI Mentor is currently unavailable. Please try again later.',
            'detail': str(e)
        }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
    except Exception as e:
        return Response({
            'error': 'Failed to process chat request.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def suggest_path(request):
    """
    Suggest learning path based on user progress.
    
    GET /api/mentor/suggest-path/
    
    Returns: {
        "suggested_skills": [
            {
                "id": 5,
                "title": "Binary Search",
                "description": "...",
                "category": "algorithms",
                "difficulty": 2,
                "xp_required": 100,
                "reason": "You've mastered arrays, binary search is the next logical step"
            }
        ],
        "reasoning": "Based on your progress...",
        "current_level": "Intermediate"
    }
    """
    user = request.user
    
    try:
        # Analyze user progress
        completed_skills = SkillProgress.objects.filter(
            user=user,
            status='completed'
        ).select_related('skill')
        
        in_progress_skills = SkillProgress.objects.filter(
            user=user,
            status='in_progress'
        ).select_related('skill')
        
        # Get total XP from submissions
        total_xp = QuestSubmission.objects.filter(
            user=user,
            status='passed'
        ).aggregate(
            total=Count('id')
        )['total'] or 0
        
        # Determine current level
        if total_xp < 5:
            current_level = "Beginner"
        elif total_xp < 15:
            current_level = "Intermediate"
        else:
            current_level = "Advanced"
        
        # Find suggested skills
        completed_skill_ids = [sp.skill.id for sp in completed_skills]
        in_progress_skill_ids = [sp.skill.id for sp in in_progress_skills]
        
        # Get skills that are unlocked but not started
        available_skills = Skill.objects.filter(
            Q(xp_required_to_unlock__lte=total_xp * 50) |  # Rough XP calculation
            Q(prerequisites__in=completed_skill_ids)
        ).exclude(
            id__in=completed_skill_ids + in_progress_skill_ids
        ).distinct()[:5]
        
        # Use RAG to find relevant skills based on completed ones
        if completed_skills.exists():
            completed_titles = ", ".join([sp.skill.title for sp in completed_skills[:3]])
            rag_results = chroma_client.query_skill_knowledge(
                f"Skills completed: {completed_titles}. What should I learn next?",
                n_results=3
            )
            
            # Extract skill IDs from RAG results
            rag_skill_ids = [
                r['metadata'].get('skill_id')
                for r in rag_results
                if r['metadata'].get('skill_id')
            ]
            
            # Prioritize RAG-suggested skills
            rag_skills = Skill.objects.filter(
                id__in=rag_skill_ids
            ).exclude(
                id__in=completed_skill_ids + in_progress_skill_ids
            )
            
            # Combine with available skills
            suggested_skills_qs = list(rag_skills) + list(available_skills)
            suggested_skills_qs = suggested_skills_qs[:5]  # Limit to 5
        else:
            suggested_skills_qs = list(available_skills)
        
        # Format suggestions with reasons
        suggested_skills = []
        for skill in suggested_skills_qs:
            # Generate reason based on prerequisites
            prereq_completed = any(
                prereq.id in completed_skill_ids
                for prereq in skill.prerequisites.all()
            )
            
            if prereq_completed:
                reason = f"You've completed the prerequisites - ready for the next challenge!"
            elif skill.difficulty <= 2:
                reason = f"Great starting point for {skill.category}"
            else:
                reason = f"Builds on your {skill.category} foundation"
            
            suggested_skills.append({
                'id': skill.id,
                'title': skill.title,
                'description': skill.description[:150] + '...' if len(skill.description) > 150 else skill.description,
                'category': skill.category,
                'difficulty': skill.difficulty,
                'xp_required': skill.xp_required_to_unlock,
                'reason': reason
            })
        
        # Generate reasoning
        if completed_skills.exists():
            completed_count = completed_skills.count()
            reasoning = f"You've completed {completed_count} skill{'s' if completed_count != 1 else ''} and earned {total_xp} quest completions. "
            
            if in_progress_skills.exists():
                reasoning += f"Continue with your in-progress skills, or explore these new challenges to expand your expertise."
            else:
                reasoning += f"Here are the next skills to level up your abilities."
        else:
            reasoning = "Welcome to SkillTree AI! Start with these foundational skills to begin your coding journey."
        
        return Response({
            'suggested_skills': suggested_skills,
            'reasoning': reasoning,
            'current_level': current_level
        }, status=status.HTTP_200_OK)
        
    except Exception as e:
        return Response({
            'error': 'Failed to generate path suggestions.',
            'detail': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def history(request):
    """
    Get user's chat history.
    
    GET /api/mentor/history/?limit=20
    
    Returns: [
        {
            "id": 123,
            "interaction_type": "explanation",
            "context_prompt": "...",
            "response": "...",
            "tokens_used": 450,
            "created_at": "2026-04-25T10:30:00Z"
        }
    ]
    """
    user = request.user
    limit = int(request.query_params.get('limit', 20))
    
    interactions = AIInteraction.objects.filter(user=user)[:limit]
    serializer = AIInteractionSerializer(interactions, many=True)
    
    return Response(serializer.data, status=status.HTTP_200_OK)


# ─── Helper Functions ─────────────────────────────────────────────────────────

def _build_rag_context(context_skill_id, context_quest_id):
    """Build RAG context from skill or quest."""
    context_parts = []
    
    if context_skill_id:
        try:
            skill = Skill.objects.get(id=context_skill_id)
            context_parts.append(f"Current Skill: {skill.title}")
            context_parts.append(f"Category: {skill.category}")
            context_parts.append(f"Description: {skill.description}")
            
            # Get RAG context from ChromaDB
            rag_results = chroma_client.query_skill_knowledge(
                f"{skill.title}: {skill.description}",
                n_results=2
            )
            
            if rag_results:
                context_parts.append("\nRelated Knowledge:")
                for i, result in enumerate(rag_results, 1):
                    context_parts.append(f"{i}. {result['document'][:200]}...")
        except Skill.DoesNotExist:
            pass
    
    if context_quest_id:
        try:
            quest = Quest.objects.select_related('skill').get(id=context_quest_id)
            context_parts.append(f"Current Quest: {quest.title}")
            context_parts.append(f"Type: {quest.type}")
            context_parts.append(f"Description: {quest.description}")
            context_parts.append(f"Related Skill: {quest.skill.title}")
        except Quest.DoesNotExist:
            pass
    
    if not context_parts:
        return "No specific context provided."
    
    return "\n".join(context_parts)


def _build_user_history(user):
    """Build summary of user's recent activity."""
    # Get recent submissions
    recent_submissions = QuestSubmission.objects.filter(
        user=user
    ).select_related('quest').order_by('-created_at')[:5]
    
    if not recent_submissions:
        return "No recent activity."
    
    history_parts = []
    passed_count = sum(1 for s in recent_submissions if s.status == 'passed')
    
    history_parts.append(f"Recent quests: {passed_count}/{len(recent_submissions)} passed")
    
    for submission in recent_submissions[:3]:
        status_emoji = "✅" if submission.status == 'passed' else "❌"
        history_parts.append(
            f"{status_emoji} {submission.quest.title} ({submission.language})"
        )
    
    return "\n".join(history_parts)
