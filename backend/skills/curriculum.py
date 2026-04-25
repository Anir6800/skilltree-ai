"""
SkillTree AI - Curriculum Generator
Builds personalized weekly learning plans with AI-generated motivational context.
"""

from celery import shared_task
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import json

from skills.models import Skill, SkillProgress
from quests.models import Quest
from users.onboarding_models import OnboardingProfile
from core.lm_client import lm_client

User = get_user_model()


class LearningCurriculum:
    """
    Model-like class for storing curriculum data.
    Stored as JSONField in user profile or separate model.
    """
    def __init__(self, user_id, weeks_data, target_completion_date=None):
        self.user_id = user_id
        self.weeks = weeks_data
        self.created_at = timezone.now()
        self.target_completion_date = target_completion_date or (
            timezone.now() + timedelta(weeks=len(weeks_data))
        )


def build_curriculum(user_id):
    """
    Generate personalized weekly curriculum for a user.
    
    Process:
    1. Load user's onboarding profile and available skills
    2. Get all quests from available skills
    3. Estimate completion time for each quest
    4. Pack quests into weekly slots based on weekly_hours budget
    5. Call LM Studio to generate motivational weekly focus summaries
    6. Save to database
    
    Args:
        user_id: User ID to generate curriculum for
        
    Returns:
        dict: {status, weeks_count, total_quests}
    """
    try:
        user = User.objects.get(id=user_id)
        
        # Get onboarding profile
        try:
            profile = user.onboarding_profile
        except OnboardingProfile.DoesNotExist:
            return {
                'status': 'error',
                'error': 'No onboarding profile found'
            }
        
        # Get available skills (status='available' or 'in_progress')
        available_skills = SkillProgress.objects.filter(
            user=user,
            status__in=['available', 'in_progress']
        ).select_related('skill')
        
        if not available_skills.exists():
            # No skills available, create default curriculum
            return _create_default_curriculum(user, profile)
        
        # Collect all quests from available skills
        all_quests = []
        for skill_progress in available_skills:
            skill = skill_progress.skill
            quests = Quest.objects.filter(skill=skill).order_by('difficulty_multiplier')
            
            for quest in quests:
                # Estimate completion time: difficulty_multiplier * 30 minutes
                est_minutes = int(quest.difficulty_multiplier * 30)
                
                all_quests.append({
                    'quest_id': quest.id,
                    'title': quest.title,
                    'skill_title': skill.title,
                    'skill_category': skill.category,
                    'est_minutes': est_minutes,
                    'xp_reward': quest.xp_reward,
                    'difficulty': quest.difficulty_multiplier,
                })
        
        if not all_quests:
            return {
                'status': 'error',
                'error': 'No quests available'
            }
        
        # Pack quests into weekly slots
        weekly_hours = profile.weekly_hours
        weekly_minutes_budget = weekly_hours * 60
        
        weeks = []
        current_week_quests = []
        current_week_minutes = 0
        week_number = 1
        
        for quest in all_quests:
            quest_minutes = quest['est_minutes']
            
            # Check if adding this quest exceeds weekly budget
            if current_week_minutes + quest_minutes > weekly_minutes_budget and current_week_quests:
                # Save current week and start new one
                weeks.append({
                    'week': week_number,
                    'quests': current_week_quests,
                    'total_minutes': current_week_minutes,
                    'focus': ''  # Will be filled by AI
                })
                week_number += 1
                current_week_quests = []
                current_week_minutes = 0
            
            # Add quest to current week
            current_week_quests.append(quest)
            current_week_minutes += quest_minutes
        
        # Add remaining quests as final week
        if current_week_quests:
            weeks.append({
                'week': week_number,
                'quests': current_week_quests,
                'total_minutes': current_week_minutes,
                'focus': ''
            })
        
        # Generate AI motivational summaries for each week
        weeks = _generate_weekly_focus(weeks, profile.target_role, profile.primary_goal)
        
        # Save curriculum to database
        from skills.models import UserCurriculum
        curriculum, created = UserCurriculum.objects.update_or_create(
            user=user,
            defaults={
                'weeks': weeks,
                'target_completion_date': timezone.now() + timedelta(weeks=len(weeks)),
                'weekly_hours': weekly_hours,
                'total_quests': len(all_quests),
            }
        )
        
        return {
            'status': 'success',
            'weeks_count': len(weeks),
            'total_quests': len(all_quests),
            'curriculum_id': curriculum.id
        }
        
    except Exception as e:
        print(f"Curriculum generation failed: {e}")
        return {
            'status': 'error',
            'error': str(e)
        }


def _generate_weekly_focus(weeks, target_role, primary_goal):
    """
    Use LM Studio to generate motivational weekly focus summaries.
    
    Args:
        weeks: List of week dictionaries
        target_role: User's target role from onboarding
        primary_goal: User's primary goal from onboarding
        
    Returns:
        List of weeks with 'focus' field populated
    """
    try:
        # Build prompt for LM Studio
        weeks_summary = []
        for week in weeks:
            quest_titles = [q['title'] for q in week['quests']]
            weeks_summary.append(f"Week {week['week']}: {', '.join(quest_titles)}")
        
        prompt = f"""You are a motivational learning coach for SkillTree AI.

User's Goal: {primary_goal}
Target Role: {target_role}

Here is the user's weekly quest schedule:

{chr(10).join(weeks_summary)}

For each week, write a 2-sentence motivational "weekly focus" summary that:
1. Connects the quests to their goal of becoming a {target_role}
2. Highlights the key skills they'll build that week
3. Keeps them motivated and excited

Return ONLY a JSON array with this exact format:
[
  {{"week": 1, "focus": "Your 2-sentence summary here"}},
  {{"week": 2, "focus": "Your 2-sentence summary here"}},
  ...
]

No other text, just the JSON array."""

        response = lm_client.chat_completion(
            messages=[
                {"role": "system", "content": "You are a motivational learning coach. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1000
        )
        
        ai_response = lm_client.extract_content(response).strip()
        
        # Parse JSON response
        try:
            # Extract JSON if wrapped in markdown code blocks
            if '```json' in ai_response:
                ai_response = ai_response.split('```json')[1].split('```')[0].strip()
            elif '```' in ai_response:
                ai_response = ai_response.split('```')[1].split('```')[0].strip()
            
            weekly_focuses = json.loads(ai_response)
            
            # Map focuses back to weeks
            focus_map = {item['week']: item['focus'] for item in weekly_focuses}
            
            for week in weeks:
                week['focus'] = focus_map.get(week['week'], 
                    f"Master the fundamentals and build towards your goal of becoming a {target_role}.")
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse AI response: {e}")
            # Fallback to generic focus messages
            for week in weeks:
                week['focus'] = f"Week {week['week']}: Build essential skills for your journey to {target_role}."
        
    except Exception as e:
        print(f"AI focus generation failed: {e}")
        # Fallback to generic messages
        for week in weeks:
            week['focus'] = f"Focus on mastering these quests to advance your skills."
    
    return weeks


def _create_default_curriculum(user, profile):
    """
    Create a default curriculum when no skills are available yet.
    """
    from skills.models import UserCurriculum
    
    default_weeks = [
        {
            'week': 1,
            'quests': [],
            'total_minutes': 0,
            'focus': f"Welcome! Complete your onboarding and unlock your first skills to begin your journey to {profile.target_role}."
        }
    ]
    
    curriculum, created = UserCurriculum.objects.update_or_create(
        user=user,
        defaults={
            'weeks': default_weeks,
            'target_completion_date': timezone.now() + timedelta(weeks=1),
            'weekly_hours': profile.weekly_hours,
            'total_quests': 0,
        }
    )
    
    return {
        'status': 'success',
        'weeks_count': 1,
        'total_quests': 0,
        'curriculum_id': curriculum.id
    }
