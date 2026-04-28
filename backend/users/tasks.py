"""
SkillTree AI - User Tasks
Celery tasks for user-related operations including weekly report generation.
"""

import logging
from celery import shared_task
from django.contrib.auth import get_user_model

from users.weekly_report import weekly_report_generator

logger = logging.getLogger(__name__)

User = get_user_model()


@shared_task(bind=True, max_retries=3)
def generate_weekly_reports_for_all_users(self):
    """
    Generate weekly reports for all active users.
    Scheduled to run every Monday at 08:00 UTC via Celery Beat.

    Retries up to 3 times on failure with exponential backoff.
    """
    try:
        users = User.objects.filter(is_active=True)
        total_users = users.count()
        successful = 0
        failed = 0

        logger.info(f"Starting weekly report generation for {total_users} users")

        for user in users:
            try:
                weekly_report_generator.generate_report(user.id)
                successful += 1
            except Exception as e:
                logger.error(f"Failed to generate report for user {user.id}: {e}")
                failed += 1

        logger.info(
            f"Weekly report generation completed: {successful} successful, {failed} failed"
        )

        return {
            'total': total_users,
            'successful': successful,
            'failed': failed
        }

    except Exception as exc:
        logger.error(f"Weekly report generation task failed: {exc}")
        raise self.retry(exc=exc, countdown=300)


@shared_task
def generate_report_for_user(user_id: int):
    """
    Generate a weekly report for a specific user.
    Can be called manually or via API.

    Args:
        user_id: ID of the user

    Returns:
        Report data with PDF path
    """
    try:
        report = weekly_report_generator.generate_report(user_id)
        logger.info(f"Generated report for user {user_id}: {report.pdf_path}")
        return {
            'report_id': report.id,
            'pdf_path': report.pdf_path,
            'week_number': report.week_number
        }
    except Exception as e:
        logger.error(f"Failed to generate report for user {user_id}: {e}")
        raise
