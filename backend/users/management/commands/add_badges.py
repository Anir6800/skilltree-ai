"""
Django management command to seed achievement badges.
"""

from django.core.management.base import BaseCommand
from users.models import Badge


class Command(BaseCommand):
    help = 'Seed achievement badges into the database'

    def handle(self, *args, **options):
        badges_data = [
            {
                'slug': 'first_blood',
                'name': 'First Blood',
                'description': 'Pass your first quest',
                'icon_emoji': '🩸',
                'rarity': 'common',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'speed_demon',
                'name': 'Speed Demon',
                'description': 'Solve a quest in the top 5% fastest time globally',
                'icon_emoji': '⚡',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'streak_lord',
                'name': 'Streak Lord',
                'description': 'Maintain a 30-day login streak',
                'icon_emoji': '🔥',
                'rarity': 'epic',
                'unlock_condition': {'event_type': 'login'},
            },
            {
                'slug': 'perfectionist',
                'name': 'Perfectionist',
                'description': '10 consecutive first-attempt quest passes',
                'icon_emoji': '✨',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'night_owl',
                'name': 'Night Owl',
                'description': 'Solve 5 quests between midnight and 5am',
                'icon_emoji': '🦉',
                'rarity': 'common',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'polyglot',
                'name': 'Polyglot',
                'description': 'Pass quests in all 5 programming languages',
                'icon_emoji': '🌐',
                'rarity': 'epic',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'tree_builder',
                'name': 'Tree Builder',
                'description': 'Generate a custom skill tree',
                'icon_emoji': '🌳',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'tree_generated'},
            },
            {
                'slug': 'mentors_pet',
                'name': "Mentor's Pet",
                'description': 'Have 10 AI mentor conversations',
                'icon_emoji': '🤖',
                'rarity': 'common',
                'unlock_condition': {'event_type': 'mentor_interaction'},
            },
            {
                'slug': 'arena_legend',
                'name': 'Arena Legend',
                'description': 'Win 50 multiplayer races',
                'icon_emoji': '⚔️',
                'rarity': 'legendary',
                'unlock_condition': {'event_type': 'race_won'},
            },
            {
                'slug': 'code_archaeologist',
                'name': 'Code Archaeologist',
                'description': 'Complete a skill 100% on first attempts',
                'icon_emoji': '🏺',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'marathon_runner',
                'name': 'Marathon Runner',
                'description': 'Complete 100 quests',
                'icon_emoji': '🏃',
                'rarity': 'epic',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'comeback_kid',
                'name': 'Comeback Kid',
                'description': 'Pass a quest after 5+ consecutive failures',
                'icon_emoji': '💪',
                'rarity': 'common',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'leaderboard_climber',
                'name': 'Leaderboard Climber',
                'description': 'Reach top 10 on the global leaderboard',
                'icon_emoji': '📈',
                'rarity': 'epic',
                'unlock_condition': {'event_type': 'leaderboard_update'},
            },
            {
                'slug': 'skill_master',
                'name': 'Skill Master',
                'description': 'Master 5 different skills',
                'icon_emoji': '🎯',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'skill_completed'},
            },
            {
                'slug': 'study_group_founder',
                'name': 'Study Group Founder',
                'description': 'Create a study group',
                'icon_emoji': '👥',
                'rarity': 'common',
                'unlock_condition': {'event_type': 'study_group_created'},
            },
            {
                'slug': 'ai_whisperer',
                'name': 'AI Whisperer',
                'description': 'Get 10 AI evaluations with score > 0.8',
                'icon_emoji': '🧠',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'bug_hunter',
                'name': 'Bug Hunter',
                'description': 'Successfully debug 20 quests',
                'icon_emoji': '🐛',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'problem_solver',
                'name': 'Problem Solver',
                'description': 'Solve 50 different quests',
                'icon_emoji': '🧩',
                'rarity': 'epic',
                'unlock_condition': {'event_type': 'quest_passed'},
            },
            {
                'slug': 'consistent_learner',
                'name': 'Consistent Learner',
                'description': 'Login 30 days in a row',
                'icon_emoji': '📚',
                'rarity': 'rare',
                'unlock_condition': {'event_type': 'login'},
            },
            {
                'slug': 'legendary_grind',
                'name': 'Legendary Grind',
                'description': 'Reach level 50',
                'icon_emoji': '👑',
                'rarity': 'legendary',
                'unlock_condition': {'event_type': 'level_up'},
            },
        ]

        created_count = 0
        for badge_data in badges_data:
            badge, created = Badge.objects.get_or_create(
                slug=badge_data['slug'],
                defaults={
                    'name': badge_data['name'],
                    'description': badge_data['description'],
                    'icon_emoji': badge_data['icon_emoji'],
                    'rarity': badge_data['rarity'],
                    'unlock_condition': badge_data['unlock_condition'],
                }
            )

            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'✓ Created badge: {badge.icon_emoji} {badge.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'- Badge already exists: {badge.icon_emoji} {badge.name}')
                )

        self.stdout.write(
            self.style.SUCCESS(f'\n✓ Created {created_count} new badges')
        )
