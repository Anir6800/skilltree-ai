"""
SkillTree AI - Admin Analytics Module
Computes quest difficulty metrics and analytics for admin dashboard.
"""

from django.db.models import Count, Q, Avg, F
from django.utils import timezone
from datetime import timedelta
from quests.models import Quest, QuestSubmission
from skills.models import Skill
from typing import List, Dict, Any


class QuestAnalytics:
    """Data class for quest analytics."""

    def __init__(
        self,
        quest_id: int,
        title: str,
        pass_rate: float,
        avg_attempts: float,
        avg_solve_time_minutes: float,
        abandonment_rate: float,
        difficulty_score: float,
        flag: str = None,
        total_submissions: int = 0,
        passed_submissions: int = 0,
    ):
        self.quest_id = quest_id
        self.title = title
        self.pass_rate = pass_rate
        self.avg_attempts = avg_attempts
        self.avg_solve_time_minutes = avg_solve_time_minutes
        self.abandonment_rate = abandonment_rate
        self.difficulty_score = difficulty_score
        self.flag = flag
        self.total_submissions = total_submissions
        self.passed_submissions = passed_submissions

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            'quest_id': self.quest_id,
            'title': self.title,
            'pass_rate': round(self.pass_rate, 2),
            'avg_attempts': round(self.avg_attempts, 2),
            'avg_solve_time_minutes': round(self.avg_solve_time_minutes, 2),
            'abandonment_rate': round(self.abandonment_rate, 2),
            'difficulty_score': round(self.difficulty_score, 2),
            'flag': self.flag,
            'total_submissions': self.total_submissions,
            'passed_submissions': self.passed_submissions,
        }


def compute_quest_analytics(skill_id: int = None) -> List[QuestAnalytics]:
    """
    Compute analytics for all quests or filtered by skill.

    Args:
        skill_id: Optional skill ID to filter quests

    Returns:
        List of QuestAnalytics objects
    """
    quests = Quest.objects.all()

    if skill_id:
        quests = quests.filter(skill_id=skill_id)

    analytics_list = []

    for quest in quests:
        submissions = quest.submissions.all()
        total_submissions = submissions.count()

        if total_submissions == 0:
            analytics = QuestAnalytics(
                quest_id=quest.id,
                title=quest.title,
                pass_rate=0.0,
                avg_attempts=0.0,
                avg_solve_time_minutes=0.0,
                abandonment_rate=0.0,
                difficulty_score=0.0,
                flag=None,
                total_submissions=0,
                passed_submissions=0,
            )
            analytics_list.append(analytics)
            continue

        passed_submissions = submissions.filter(status='passed').count()
        pass_rate = (passed_submissions / total_submissions) * 100 if total_submissions > 0 else 0

        users_started = submissions.values('user').distinct().count()
        users_passed = submissions.filter(status='passed').values('user').distinct().count()
        abandonment_rate = (
            (users_started - users_passed) / users_started if users_started > 0 else 0
        )

        avg_attempts = 0.0
        if users_passed > 0:
            attempts_per_user = {}
            for submission in submissions.filter(status='passed'):
                user_id = submission.user_id
                if user_id not in attempts_per_user:
                    attempts_per_user[user_id] = 0
                attempts_per_user[user_id] += 1

            if attempts_per_user:
                avg_attempts = sum(attempts_per_user.values()) / len(attempts_per_user)

        avg_solve_time_minutes = 0.0
        passed_subs = submissions.filter(status='passed')
        if passed_subs.exists():
            solve_times = []
            for submission in passed_subs:
                if submission.created_at:
                    time_diff = timezone.now() - submission.created_at
                    solve_times.append(time_diff.total_seconds() / 60)

            if solve_times:
                avg_solve_time_minutes = sum(solve_times) / len(solve_times)

        difficulty_score = (
            (1 - (pass_rate / 100)) * 0.5
            + (min(avg_attempts / 10, 1.0)) * 0.3
            + abandonment_rate * 0.2
        )

        flag = None
        if difficulty_score > 0.8:
            flag = 'too_hard'
        elif difficulty_score < 0.15:
            flag = 'too_easy'

        analytics = QuestAnalytics(
            quest_id=quest.id,
            title=quest.title,
            pass_rate=pass_rate,
            avg_attempts=avg_attempts,
            avg_solve_time_minutes=avg_solve_time_minutes,
            abandonment_rate=abandonment_rate,
            difficulty_score=difficulty_score,
            flag=flag,
            total_submissions=total_submissions,
            passed_submissions=passed_submissions,
        )
        analytics_list.append(analytics)

    return analytics_list


def get_heatmap_summary(analytics_list: List[QuestAnalytics]) -> Dict[str, Any]:
    """
    Get summary statistics for heatmap.

    Args:
        analytics_list: List of QuestAnalytics objects

    Returns:
        Dictionary with summary counts
    """
    too_hard_count = sum(1 for a in analytics_list if a.flag == 'too_hard')
    too_easy_count = sum(1 for a in analytics_list if a.flag == 'too_easy')
    healthy_count = len(analytics_list) - too_hard_count - too_easy_count

    return {
        'too_hard_count': too_hard_count,
        'too_easy_count': too_easy_count,
        'healthy_count': healthy_count,
        'total_quests': len(analytics_list),
    }
