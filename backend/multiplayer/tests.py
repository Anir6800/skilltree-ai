from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from multiplayer.models import Match, MatchParticipant
from quests.models import Quest
from skills.models import Skill

User = get_user_model()


class MatchModelTest(TestCase):
    """Test Match model functionality."""
    
    def setUp(self):
        self.user1 = User.objects.create_user(username='player1', password='test123')
        self.user2 = User.objects.create_user(username='player2', password='test123')
        self.skill = Skill.objects.create(title='Python Basics', description='Learn Python')
        self.quest = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='Test Quest',
            description='A test quest',
            xp_reward=100
        )
    
    def test_create_match(self):
        """Test creating a match."""
        match = Match.objects.create(quest=self.quest, status='waiting')
        self.assertEqual(match.status, 'waiting')
        self.assertIsNone(match.winner)
    
    def test_add_participants(self):
        """Test adding participants to a match."""
        match = Match.objects.create(quest=self.quest, status='waiting')
        MatchParticipant.objects.create(match=match, user=self.user1)
        MatchParticipant.objects.create(match=match, user=self.user2)
        
        self.assertEqual(match.participants.count(), 2)
        self.assertIn(self.user1, match.participants.all())
        self.assertIn(self.user2, match.participants.all())


class MatchAPITest(APITestCase):
    """Test Match API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user1 = User.objects.create_user(username='player1', password='test123')
        self.user2 = User.objects.create_user(username='player2', password='test123')
        self.skill = Skill.objects.create(title='Python Basics', description='Learn Python')
        self.quest = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='Test Quest',
            description='A test quest',
            xp_reward=100,
            starter_code='# Write your code here',
            test_cases=[{'input': '1', 'expected_output': '1'}]
        )
    
    def test_create_match_authenticated(self):
        """Test creating a match as authenticated user."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post('/api/matches/', {
            'quest_id': self.quest.id,
            'max_participants': 2
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('invite_code', response.data)
        self.assertEqual(response.data['status'], 'waiting')
    
    def test_create_match_unauthenticated(self):
        """Test creating a match without authentication."""
        response = self.client.post('/api/matches/', {
            'quest_id': self.quest.id,
            'max_participants': 2
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_join_match(self):
        """Test joining a match with invite code."""
        # User 1 creates match
        self.client.force_authenticate(user=self.user1)
        create_response = self.client.post('/api/matches/', {
            'quest_id': self.quest.id,
            'max_participants': 2
        })
        invite_code = create_response.data['invite_code']
        
        # User 2 joins match
        self.client.force_authenticate(user=self.user2)
        join_response = self.client.post('/api/matches/join/', {
            'invite_code': invite_code
        })
        
        self.assertEqual(join_response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(join_response.data['participants']), 2)
    
    def test_join_match_invalid_code(self):
        """Test joining with invalid invite code."""
        self.client.force_authenticate(user=self.user1)
        
        response = self.client.post('/api/matches/join/', {
            'invite_code': 'INVALID-CODE'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_matches(self):
        """Test listing open matches."""
        # Create a match
        match = Match.objects.create(quest=self.quest, status='waiting')
        MatchParticipant.objects.create(match=match, user=self.user1)
        
        self.client.force_authenticate(user=self.user2)
        response = self.client.get('/api/matches/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data['results']), 1)
    
    def test_get_match_detail(self):
        """Test getting match details."""
        match = Match.objects.create(quest=self.quest, status='waiting')
        MatchParticipant.objects.create(match=match, user=self.user1)
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/matches/{match.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['id'], match.id)
        self.assertEqual(response.data['status'], 'waiting')
    
    def test_leave_match(self):
        """Test leaving a match."""
        match = Match.objects.create(quest=self.quest, status='waiting')
        MatchParticipant.objects.create(match=match, user=self.user1)
        MatchParticipant.objects.create(match=match, user=self.user2)
        
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f'/api/matches/{match.id}/leave/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        match.refresh_from_db()
        self.assertEqual(match.participants.count(), 1)
    
    def test_match_status(self):
        """Test getting match status."""
        match = Match.objects.create(quest=self.quest, status='waiting')
        MatchParticipant.objects.create(match=match, user=self.user1)
        
        self.client.force_authenticate(user=self.user1)
        response = self.client.get(f'/api/matches/{match.id}/status/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['status'], 'waiting')
        self.assertEqual(len(response.data['participants']), 1)
