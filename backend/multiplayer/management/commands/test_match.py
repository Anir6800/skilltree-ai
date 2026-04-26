from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from multiplayer.models import Match, MatchParticipant
from quests.models import Quest
from skills.models import Skill

User = get_user_model()


class Command(BaseCommand):
    help = 'Create a test match for development and testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=2,
            help='Number of test users to create (default: 2)'
        )
        parser.add_argument(
            '--quest-id',
            type=int,
            help='Quest ID to use for the match (creates one if not specified)'
        )

    def handle(self, *args, **options):
        num_users = options['users']
        quest_id = options.get('quest_id')

        self.stdout.write(self.style.SUCCESS('Creating test match...'))

        # Create or get quest
        if quest_id:
            try:
                quest = Quest.objects.get(id=quest_id)
                self.stdout.write(f'Using existing quest: {quest.title}')
            except Quest.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'Quest with ID {quest_id} not found'))
                return
        else:
            # Create a test skill and quest
            skill, _ = Skill.objects.get_or_create(
                title='Test Skill',
                defaults={
                    'description': 'A test skill for multiplayer matches',
                    'category': 'programming'
                }
            )
            
            quest, created = Quest.objects.get_or_create(
                title='Test Multiplayer Quest',
                defaults={
                    'skill': skill,
                    'type': 'coding',
                    'description': 'Write a function that returns the sum of two numbers',
                    'starter_code': 'def add(a, b):\n    # Your code here\n    pass',
                    'test_cases': [
                        {'input': '1, 2', 'expected_output': '3'},
                        {'input': '5, 7', 'expected_output': '12'},
                        {'input': '0, 0', 'expected_output': '0'},
                    ],
                    'xp_reward': 100,
                    'estimated_minutes': 10,
                    'difficulty_multiplier': 1.0
                }
            )
            
            if created:
                self.stdout.write(f'Created test quest: {quest.title}')
            else:
                self.stdout.write(f'Using existing test quest: {quest.title}')

        # Create test users
        users = []
        for i in range(1, num_users + 1):
            username = f'testplayer{i}'
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f'{username}@test.com',
                    'xp': 100 * i,
                    'level': i
                }
            )
            
            if created:
                user.set_password('test123')
                user.save()
                self.stdout.write(f'Created user: {username} (password: test123)')
            else:
                self.stdout.write(f'Using existing user: {username}')
            
            users.append(user)

        # Create match
        match = Match.objects.create(
            quest=quest,
            status='waiting'
        )

        # Add participants
        for user in users:
            MatchParticipant.objects.create(
                match=match,
                user=user
            )

        self.stdout.write(self.style.SUCCESS(f'\n✅ Test match created successfully!'))
        self.stdout.write(f'\nMatch ID: {match.id}')
        self.stdout.write(f'Invite Code: MATCH-{match.id}')
        self.stdout.write(f'Quest: {quest.title}')
        self.stdout.write(f'Participants: {", ".join([u.username for u in users])}')
        self.stdout.write(f'\nWebSocket URL: ws://localhost:8000/ws/match/{match.id}/?token=<JWT_TOKEN>')
        self.stdout.write(f'API URL: http://localhost:8000/api/matches/{match.id}/')
        
        self.stdout.write(self.style.WARNING('\nTo get JWT tokens for testing:'))
        for user in users:
            self.stdout.write(f'  curl -X POST http://localhost:8000/api/token/ -H "Content-Type: application/json" -d \'{{"username": "{user.username}", "password": "test123"}}\'')
