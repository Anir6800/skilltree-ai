"""
SkillTree AI - Weekly Report Generator
Generates comprehensive weekly progress reports with LM Studio narratives and ReportLab PDFs.
Scheduled via Celery Beat every Monday at 08:00 UTC.
"""

import logging
import json
import os
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from django.conf import settings
from django.utils import timezone
from django.db.models import Q, Sum, Count
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib.colors import HexColor
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, Image
from reportlab.lib import colors
from reportlab.graphics.shapes import Drawing
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics.charts.legends import Legend

from core.lm_client import lm_client, ExecutionServiceUnavailable
from quests.models import QuestSubmission
from skills.models import Skill, SkillProgress
from users.models import User, UserBadge, XPLog

logger = logging.getLogger(__name__)


class WeeklyReportGenerator:
    """
    Generates comprehensive weekly progress reports for users.
    Collects data from last 7 days and creates PDF with AI narrative.
    """

    def __init__(self):
        """Initialize report generator with LM Studio client."""
        self.client = lm_client
        self.reports_dir = Path(settings.MEDIA_ROOT) / 'reports'
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def generate_report(self, user_id: int) -> 'WeeklyReport':
        """
        Generate a weekly report for a user.

        Args:
            user_id: ID of the user

        Returns:
            WeeklyReport object with PDF path

        Raises:
            User.DoesNotExist: If user not found
            ExecutionServiceUnavailable: If LM Studio unavailable
        """
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            raise ValueError(f"User with ID {user_id} not found")

        now = timezone.now()
        week_start = now - timedelta(days=now.weekday())
        week_end = week_start + timedelta(days=7)
        iso_week = now.isocalendar()[1]

        data = self._collect_week_data(user, week_start, week_end)

        narrative = self._generate_narrative(user, data)

        pdf_path = self._generate_pdf(user, data, narrative, week_start, week_end)

        from users.models import WeeklyReport
        report = WeeklyReport.objects.create(
            user=user,
            week_number=iso_week,
            pdf_path=pdf_path,
            data=data,
            narrative=narrative
        )

        logger.info(f"Generated weekly report for {user.username} (Week {iso_week})")
        return report

    def _collect_week_data(self, user: User, week_start: datetime, week_end: datetime) -> dict:
        """
        Collect all relevant data for the week.

        Returns dict with:
        - quests_passed, quests_failed, xp_earned, skills_unlocked, badges_earned
        - streak_days, multiplayer_wins, time_spent_minutes, best_skill_category
        - daily_xp (list of 7 values), skill_breakdown (dict)
        """
        submissions = QuestSubmission.objects.filter(
            user=user,
            created_at__gte=week_start,
            created_at__lt=week_end
        )

        quests_passed = submissions.filter(status='passed').count()
        quests_failed = submissions.filter(status__in=['failed', 'flagged']).count()

        xp_logs = XPLog.objects.filter(
            user=user,
            created_at__gte=week_start,
            created_at__lt=week_end
        )
        xp_earned = xp_logs.aggregate(total=Sum('amount'))['total'] or 0

        badges_earned = UserBadge.objects.filter(
            user=user,
            earned_at__gte=week_start,
            earned_at__lt=week_end
        ).count()

        skills_unlocked = SkillProgress.objects.filter(
            user=user,
            status='completed',
            completed_at__gte=week_start,
            completed_at__lt=week_end
        ).count()

        time_spent_ms = submissions.aggregate(
            total=Sum('execution_result__time_ms')
        )['total'] or 0
        time_spent_minutes = int(time_spent_ms / 60000)

        daily_xp = self._calculate_daily_xp(xp_logs, week_start)

        skill_breakdown = self._calculate_skill_breakdown(submissions)

        best_skill_category = max(
            skill_breakdown.items(),
            key=lambda x: x[1]['passed'],
            default=('unknown', {'passed': 0, 'failed': 0})
        )[0]

        multiplayer_wins = 0

        return {
            'quests_passed': quests_passed,
            'quests_failed': quests_failed,
            'xp_earned': xp_earned,
            'skills_unlocked': skills_unlocked,
            'badges_earned': badges_earned,
            'streak_days': user.streak_days,
            'multiplayer_wins': multiplayer_wins,
            'time_spent_minutes': time_spent_minutes,
            'best_skill_category': best_skill_category,
            'daily_xp': daily_xp,
            'skill_breakdown': skill_breakdown,
            'total_quests': quests_passed + quests_failed,
            'win_rate': round(
                (quests_passed / (quests_passed + quests_failed) * 100) if (quests_passed + quests_failed) > 0 else 0,
                1
            )
        }

    def _calculate_daily_xp(self, xp_logs, week_start: datetime) -> list:
        """Calculate XP earned for each day of the week."""
        daily_xp = [0] * 7

        for log in xp_logs:
            day_offset = (log.created_at.date() - week_start.date()).days
            if 0 <= day_offset < 7:
                daily_xp[day_offset] += log.amount

        return daily_xp

    def _calculate_skill_breakdown(self, submissions) -> dict:
        """Calculate passed/failed quests by skill category."""
        breakdown = {}

        for submission in submissions:
            category = submission.quest.skill.category
            if category not in breakdown:
                breakdown[category] = {'passed': 0, 'failed': 0}

            if submission.status == 'passed':
                breakdown[category]['passed'] += 1
            else:
                breakdown[category]['failed'] += 1

        return breakdown

    def _generate_narrative(self, user: User, data: dict) -> dict:
        """
        Generate AI narrative sections using LM Studio.

        Returns dict with: opening_sentence, skill_analysis, recommendation, motivational_close
        """
        prompt = self._build_narrative_prompt(user, data)

        messages = [
            {
                "role": "system",
                "content": "You are a motivational coding mentor. Generate a weekly progress report narrative. Respond ONLY in valid JSON with no markdown or extra text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ]

        try:
            response = self.client.chat_completion(
                messages=messages,
                max_tokens=1000,
                temperature=0.7,
                response_format={"type": "json_object"}
            )

            content = self.client.extract_content(response)
            narrative = json.loads(content)

            self._validate_narrative(narrative)

            return narrative

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse narrative JSON: {e}")
            return self._get_fallback_narrative(user, data)
        except ExecutionServiceUnavailable as e:
            logger.error(f"LM Studio unavailable for narrative: {e}")
            return self._get_fallback_narrative(user, data)
        except Exception as e:
            logger.error(f"Narrative generation failed: {e}")
            return self._get_fallback_narrative(user, data)

    def _build_narrative_prompt(self, user: User, data: dict) -> str:
        """Build prompt for LM Studio narrative generation."""
        json_data = json.dumps(data, indent=2)

        prompt = f"""Write a weekly progress report for a developer named {user.username}.

Data:
{json_data}

Generate a JSON response with exactly these fields:
1. "opening_sentence": One motivational sentence referencing their best achievement this week
2. "skill_analysis": Two sentences analyzing their strongest and weakest skill categories
3. "recommendation": Exactly 3 specific quest titles they should tackle next week based on weak spots
4. "motivational_close": One sentence to motivate them for next week

Respond ONLY with valid JSON, no markdown or extra text."""

        return prompt

    def _validate_narrative(self, narrative: dict) -> None:
        """Validate narrative has all required fields."""
        required_fields = ['opening_sentence', 'skill_analysis', 'recommendation', 'motivational_close']

        for field in required_fields:
            if field not in narrative:
                raise ValueError(f"Missing narrative field: {field}")

            if not isinstance(narrative[field], str) or len(narrative[field]) < 5:
                raise ValueError(f"Invalid {field}: must be non-empty string")

    def _get_fallback_narrative(self, user: User, data: dict) -> dict:
        """Return fallback narrative when LM Studio unavailable."""
        return {
            'opening_sentence': f"Great week, {user.username}! You earned {data['xp_earned']} XP and passed {data['quests_passed']} quests.",
            'skill_analysis': f"Your strongest area is {data['best_skill_category']}. Keep pushing on your weaker categories to build well-rounded skills.",
            'recommendation': "Focus on foundational concepts, practice debugging, and tackle one advanced challenge.",
            'motivational_close': "You're building momentum—keep up the consistent effort next week!"
        }

    def _generate_pdf(self, user: User, data: dict, narrative: dict, week_start: datetime, week_end: datetime) -> str:
        """
        Generate PDF report using ReportLab.

        Returns path to saved PDF file.
        """
        user_reports_dir = self.reports_dir / str(user.id)
        user_reports_dir.mkdir(parents=True, exist_ok=True)

        iso_week = week_start.isocalendar()[1]
        pdf_filename = f"week_{iso_week}.pdf"
        pdf_path = user_reports_dir / pdf_filename

        doc = SimpleDocTemplate(
            str(pdf_path),
            pagesize=letter,
            rightMargin=0.5*inch,
            leftMargin=0.5*inch,
            topMargin=0.5*inch,
            bottomMargin=0.5*inch
        )

        story = []
        styles = getSampleStyleSheet()

        story.extend(self._build_header(user, week_start, week_end, styles))
        story.append(Spacer(1, 0.2*inch))

        story.extend(self._build_stats_grid(data, styles))
        story.append(Spacer(1, 0.2*inch))

        story.extend(self._build_chart(data, styles))
        story.append(Spacer(1, 0.2*inch))

        story.extend(self._build_narrative_section(narrative, styles))
        story.append(Spacer(1, 0.2*inch))

        story.extend(self._build_recommendations(narrative, styles))

        doc.build(story)

        relative_path = f"reports/{user.id}/{pdf_filename}"
        return relative_path

    def _build_header(self, user: User, week_start: datetime, week_end: datetime, styles) -> list:
        """Build PDF header section."""
        story = []

        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=HexColor('#7c6af5'),
            spaceAfter=6,
            fontName='Helvetica-Bold'
        )

        subtitle_style = ParagraphStyle(
            'CustomSubtitle',
            parent=styles['Normal'],
            fontSize=12,
            textColor=HexColor('#9ca3af'),
            spaceAfter=12
        )

        title = Paragraph("🌳 SkillTree AI — Weekly Report", title_style)
        story.append(title)

        date_range = f"{week_start.strftime('%b %d')} — {week_end.strftime('%b %d, %Y')}"
        subtitle = Paragraph(f"Week of {date_range} • {user.username}", subtitle_style)
        story.append(subtitle)

        return story

    def _build_stats_grid(self, data: dict, styles) -> list:
        """Build 6-metric stats grid."""
        story = []

        metrics = [
            ('XP Earned', f"{data['xp_earned']}", '#10b981'),
            ('Quests Passed', f"{data['quests_passed']}", '#3b82f6'),
            ('Skills Unlocked', f"{data['skills_unlocked']}", '#f59e0b'),
            ('Streak', f"{data['streak_days']} days", '#ec4899'),
            ('Win Rate', f"{data['win_rate']}%", '#8b5cf6'),
            ('Time Coded', f"{data['time_spent_minutes']} min", '#06b6d4'),
        ]

        cells = []
        for label, value, color in metrics:
            cell_data = [
                [Paragraph(f"<b>{value}</b>", ParagraphStyle(
                    'MetricValue',
                    parent=styles['Normal'],
                    fontSize=16,
                    textColor=HexColor(color),
                    alignment=1
                ))],
                [Paragraph(label, ParagraphStyle(
                    'MetricLabel',
                    parent=styles['Normal'],
                    fontSize=10,
                    textColor=HexColor('#9ca3af'),
                    alignment=1
                ))]
            ]
            cells.append(cell_data)

        table_data = [cells[i:i+3] for i in range(0, len(cells), 3)]

        table = Table(table_data, colWidths=[1.8*inch]*3)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, -1), HexColor('#1a1d29')),
            ('BORDER', (0, 0), (-1, -1), 1, HexColor('#374151')),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('LEFTPADDING', (0, 0), (-1, -1), 10),
            ('RIGHTPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))

        story.append(table)
        return story

    def _build_chart(self, data: dict, styles) -> list:
        """Build daily XP bar chart."""
        story = []

        drawing = Drawing(6*inch, 2.5*inch)

        chart = VerticalBarChart()
        chart.x = 0.5*inch
        chart.y = 0.3*inch
        chart.width = 5*inch
        chart.height = 2*inch

        chart.data = [data['daily_xp']]
        chart.categoryAxis.categoryNames = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
        chart.categoryAxis.labels.fontSize = 9
        chart.categoryAxis.labels.textColor = HexColor('#9ca3af')

        chart.valueAxis.labels.fontSize = 9
        chart.valueAxis.labels.textColor = HexColor('#9ca3af')

        chart.bars[0].fillColor = HexColor('#7c6af5')

        drawing.add(chart)

        story.append(drawing)
        return story

    def _build_narrative_section(self, narrative: dict, styles) -> list:
        """Build AI narrative sections."""
        story = []

        section_style = ParagraphStyle(
            'NarrativeSection',
            parent=styles['Normal'],
            fontSize=11,
            textColor=HexColor('#e5e7eb'),
            spaceAfter=12,
            leading=16
        )

        story.append(Paragraph(f"<b>✨ Your Week</b>", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#7c6af5'),
            spaceAfter=8
        )))

        story.append(Paragraph(narrative['opening_sentence'], section_style))
        story.append(Spacer(1, 0.1*inch))

        story.append(Paragraph(f"<b>📊 Skill Analysis</b>", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#7c6af5'),
            spaceAfter=8
        )))

        story.append(Paragraph(narrative['skill_analysis'], section_style))
        story.append(Spacer(1, 0.1*inch))

        story.append(Paragraph(f"<b>🚀 Next Week</b>", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#7c6af5'),
            spaceAfter=8
        )))

        story.append(Paragraph(narrative['motivational_close'], section_style))

        return story

    def _build_recommendations(self, narrative: dict, styles) -> list:
        """Build next week recommendations section."""
        story = []

        story.append(Paragraph(f"<b>📋 Recommended Quests</b>", ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#7c6af5'),
            spaceAfter=8
        )))

        recommendations = narrative.get('recommendation', 'Focus on foundational concepts')
        if isinstance(recommendations, str):
            rec_list = [r.strip() for r in recommendations.split(',')][:3]
        else:
            rec_list = recommendations if isinstance(recommendations, list) else []

        for i, rec in enumerate(rec_list, 1):
            story.append(Paragraph(f"{i}. {rec}", ParagraphStyle(
                'RecommendationItem',
                parent=styles['Normal'],
                fontSize=10,
                textColor=HexColor('#d1d5db'),
                spaceAfter=6,
                leftIndent=0.2*inch
            )))

        return story


weekly_report_generator = WeeklyReportGenerator()
