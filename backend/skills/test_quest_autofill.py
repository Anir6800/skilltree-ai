"""
Tests for QuestAutoFillService
Validates quest generation, validation, and WebSocket broadcasting.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase
from django.contrib.auth import get_user_model
from django.utils import timezone

from skills.models import GeneratedSkillTree, Skill
from quests.models import Quest
from skills.quest_autofill import QuestAutoFillService

User = get_user_model()


class QuestAutoFillServiceTestCase(TestCase):
    """Test suite for QuestAutoFillService"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.tree = GeneratedSkillTree.objects.create(
            topic='Python Basics',
            created_by=self.user,
            status='ready',
            raw_ai_response={'skills': []}
        )
        
        self.skill = Skill.objects.create(
            title='Variables',
            description='Learn about variables in Python',
            category='custom_python_basics',
            difficulty=1
        )
        
        self.tree.skills_created.add(self.skill)
        
        # Create stub quest
        self.quest = Quest.objects.create(
            skill=self.skill,
            type='coding',
            title='Create a Variable',
            description='Complete this quest to master Variables',
            starter_code='',
            test_cases=[],
            xp_reward=50,
            estimated_minutes=15,
            difficulty_multiplier=1.0
        )
        
        self.service = QuestAutoFillService()
    
    def test_autofill_quests_for_tree_not_found(self):
        """Test error handling when tree doesn't exist"""
        with self.assertRaises(ValueError) as context:
            self.service.autofill_quests_for_tree('invalid-id')
        
        self.assertIn('not found', str(context.exception))
    
    def test_autofill_quests_for_tree_wrong_status(self):
        """Test error handling when tree is not ready"""
        tree = GeneratedSkillTree.objects.create(
            topic='Test',
            created_by=self.user,
            status='generating'
        )
        
        with self.assertRaises(ValueError) as context:
            self.service.autofill_quests_for_tree(str(tree.id))
        
        self.assertIn('ready', str(context.exception))
    
    def test_autofill_quests_for_tree_no_stubs(self):
        """Test when there are no stub quests"""
        # Fill the quest so it's not a stub
        self.quest.test_cases = [
            {'input': '1', 'expected_output': '1'}
        ]
        self.quest.save()
        
        result = self.service.autofill_quests_for_tree(str(self.tree.id))
        
        self.assertEqual(result['status'], 'no_quests')
        self.assertEqual(result['quests_to_fill'], 0)
    
    def test_build_quest_prompt(self):
        """Test quest prompt generation"""
        prompt = self.service._build_quest_prompt(
            'Variables',
            'Create a Variable',
            1
        )
        
        self.assertIn('Variables', prompt)
        self.assertIn('Create a Variable', prompt)
        self.assertIn('1/5', prompt)
        self.assertIn('JSON', prompt)
    
    def test_extract_json_with_markdown(self):
        """Test JSON extraction from markdown code blocks"""
        content = '```json\n{"test": "value"}\n```'
        result = self.service._extract_json(content)
        
        self.assertEqual(result, {"test": "value"})
    
    def test_extract_json_plain(self):
        """Test JSON extraction from plain JSON"""
        content = '{"test": "value"}'
        result = self.service._extract_json(content)
        
        self.assertEqual(result, {"test": "value"})
    
    def test_extract_json_invalid(self):
        """Test JSON extraction with invalid JSON"""
        content = 'not json'
        result = self.service._extract_json(content)
        
        self.assertIsNone(result)
    
    def test_validate_quest_data_valid_coding(self):
        """Test validation of valid coding quest data"""
        quest_data = {
            'description': 'This is a test quest description',
            'type': 'coding',
            'xp_reward': 100,
            'difficulty_multiplier': 1.5,
            'test_cases': [
                {'input': '1', 'expected_output': '1', 'description': 'test'},
                {'input': '2', 'expected_output': '2', 'description': 'test'},
                {'input': '3', 'expected_output': '3', 'description': 'test'},
            ]
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_quest_data_invalid_type(self):
        """Test validation with invalid quest type"""
        quest_data = {
            'description': 'Test',
            'type': 'invalid_type',
            'xp_reward': 100,
            'difficulty_multiplier': 1.0
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertFalse(is_valid)
        self.assertIn('Invalid quest type', error)
    
    def test_validate_quest_data_invalid_xp(self):
        """Test validation with invalid XP reward"""
        quest_data = {
            'description': 'Test',
            'type': 'coding',
            'xp_reward': 1000,  # Too high
            'difficulty_multiplier': 1.0
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertFalse(is_valid)
        self.assertIn('XP reward', error)
    
    def test_validate_quest_data_invalid_difficulty_multiplier(self):
        """Test validation with invalid difficulty multiplier"""
        quest_data = {
            'description': 'Test',
            'type': 'coding',
            'xp_reward': 100,
            'difficulty_multiplier': 5.0  # Too high
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertFalse(is_valid)
        self.assertIn('Difficulty multiplier', error)
    
    def test_validate_quest_data_insufficient_test_cases(self):
        """Test validation with insufficient test cases for coding quest"""
        quest_data = {
            'description': 'Test',
            'type': 'coding',
            'xp_reward': 100,
            'difficulty_multiplier': 1.0,
            'test_cases': [
                {'input': '1', 'expected_output': '1'}
            ]
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertFalse(is_valid)
        self.assertIn('at least 3 test cases', error)
    
    def test_validate_quest_data_valid_mcq(self):
        """Test validation of valid MCQ quest data"""
        quest_data = {
            'description': 'What is 2+2?',
            'type': 'mcq',
            'xp_reward': 50,
            'difficulty_multiplier': 1.0,
            'mcq_options': ['3', '4', '5', '6'],
            'correct_answer': '4'
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertTrue(is_valid)
        self.assertIsNone(error)
    
    def test_validate_quest_data_invalid_mcq_options(self):
        """Test validation with invalid MCQ options"""
        quest_data = {
            'description': 'What is 2+2?',
            'type': 'mcq',
            'xp_reward': 50,
            'difficulty_multiplier': 1.0,
            'mcq_options': ['3', '4', '5'],  # Only 3 options
            'correct_answer': '4'
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertFalse(is_valid)
        self.assertIn('exactly 4 options', error)
    
    def test_validate_quest_data_invalid_correct_answer(self):
        """Test validation with invalid correct answer"""
        quest_data = {
            'description': 'What is 2+2?',
            'type': 'mcq',
            'xp_reward': 50,
            'difficulty_multiplier': 1.0,
            'mcq_options': ['3', '4', '5', '6'],
            'correct_answer': '7'  # Not in options
        }
        
        is_valid, error = self.service._validate_quest_data(quest_data)
        
        self.assertFalse(is_valid)
        self.assertIn('one of the options', error)
    
    @patch('skills.quest_autofill.lm_client.chat_completion')
    def test_call_lm_studio_for_quest_success(self, mock_chat):
        """Test successful LM Studio call"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'description': 'Create a variable',
                        'type': 'coding',
                        'xp_reward': 100,
                        'difficulty_multiplier': 1.0,
                        'test_cases': [
                            {'input': '1', 'expected_output': '1'},
                            {'input': '2', 'expected_output': '2'},
                            {'input': '3', 'expected_output': '3'},
                        ]
                    })
                }
            }]
        }
        mock_chat.return_value = mock_response
        
        result = self.service._call_lm_studio_for_quest('Variables', 'Create a Variable', 1)
        
        self.assertEqual(result['type'], 'coding')
        self.assertEqual(result['xp_reward'], 100)
        self.assertEqual(len(result['test_cases']), 3)
    
    @patch('skills.quest_autofill.lm_client.chat_completion')
    def test_call_lm_studio_for_quest_failure(self, mock_chat):
        """Test LM Studio call failure"""
        from core.lm_client import ExecutionServiceUnavailable
        
        mock_chat.side_effect = ExecutionServiceUnavailable('Service unavailable')
        
        with self.assertRaises(ValueError):
            self.service._call_lm_studio_for_quest('Variables', 'Create a Variable', 1)
    
    @patch('skills.quest_autofill.lm_client.chat_completion')
    def test_fill_quest_success(self, mock_chat):
        """Test successful quest filling"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'description': 'Create a variable to store your name',
                        'type': 'coding',
                        'starter_code': 'name = # TODO: assign your name',
                        'xp_reward': 100,
                        'difficulty_multiplier': 1.0,
                        'test_cases': [
                            {'input': '', 'expected_output': 'name assigned', 'description': 'test 1'},
                            {'input': '', 'expected_output': 'name assigned', 'description': 'test 2'},
                            {'input': '', 'expected_output': 'name assigned', 'description': 'test 3'},
                        ]
                    })
                }
            }]
        }
        mock_chat.return_value = mock_response
        
        success, error = self.service._fill_quest(self.quest, str(self.tree.id), self.user.id)
        
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # Verify quest was updated
        self.quest.refresh_from_db()
        self.assertNotEqual(self.quest.description, 'Complete this quest to master Variables')
        self.assertEqual(len(self.quest.test_cases), 3)
        self.assertEqual(self.quest.xp_reward, 100)
    
    @patch('skills.quest_autofill.lm_client.chat_completion')
    def test_execute_autofill_success(self, mock_chat):
        """Test successful autofill execution"""
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'description': 'Create a variable',
                        'type': 'coding',
                        'xp_reward': 100,
                        'difficulty_multiplier': 1.0,
                        'test_cases': [
                            {'input': '1', 'expected_output': '1'},
                            {'input': '2', 'expected_output': '2'},
                            {'input': '3', 'expected_output': '3'},
                        ]
                    })
                }
            }]
        }
        mock_chat.return_value = mock_response
        
        result = self.service.execute_autofill(str(self.tree.id))
        
        self.assertEqual(result['status'], 'completed')
        self.assertEqual(result['quests_filled'], 1)
        self.assertEqual(result['total_quests'], 1)
    
    def test_execute_autofill_tree_not_found(self):
        """Test autofill with non-existent tree"""
        result = self.service.execute_autofill('invalid-id')
        
        self.assertEqual(result['status'], 'failed')
        self.assertIn('not found', result['error'])
