"""
Tests for AI Skill Tree Generator
Tests LM Studio integration, prerequisite resolution, and API endpoints.
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status

from skills.models import Skill, SkillPrerequisite, GeneratedSkillTree
from skills.ai_tree_generator import SkillTreeGeneratorService
from quests.models import Quest

User = get_user_model()


class SkillTreeGeneratorServiceTests(TestCase):
    """Test SkillTreeGeneratorService core functionality."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.service = SkillTreeGeneratorService()
    
    def test_generate_tree_creates_record(self):
        """Test that generate_tree creates a GeneratedSkillTree record."""
        result = self.service.generate_tree(
            topic="Python Basics",
            user=self.user,
            depth=2
        )
        
        self.assertEqual(result['status'], 'generating')
        self.assertIn('tree_id', result)
        
        tree = GeneratedSkillTree.objects.get(id=result['tree_id'])
        self.assertEqual(tree.topic, "Python Basics")
        self.assertEqual(tree.created_by, self.user)
        self.assertEqual(tree.status, "generating")
    
    def test_generate_tree_validates_topic(self):
        """Test that generate_tree validates topic input."""
        with self.assertRaises(ValueError):
            self.service.generate_tree(topic="", user=self.user)
        
        with self.assertRaises(ValueError):
            self.service.generate_tree(topic="   ", user=self.user)
    
    def test_generate_tree_validates_depth(self):
        """Test that generate_tree validates depth input."""
        with self.assertRaises(ValueError):
            self.service.generate_tree(topic="Test", user=self.user, depth=0)
        
        with self.assertRaises(ValueError):
            self.service.generate_tree(topic="Test", user=self.user, depth=6)
    
    def test_build_user_prompt(self):
        """Test that user prompt is correctly formatted."""
        prompt = self.service._build_user_prompt("Machine Learning", 3)
        
        self.assertIn("Machine Learning", prompt)
        self.assertIn("Depth: 3", prompt)
        self.assertIn("6–12 skills", prompt)
        self.assertIn("prerequisites", prompt)
        self.assertIn("quest_titles", prompt)
    
    def test_extract_json_from_markdown(self):
        """Test JSON extraction from markdown code blocks."""
        content = """
        ```json
        {"skills": [{"title": "Test"}]}
        ```
        """
        result = self.service._extract_json(content)
        self.assertEqual(result['skills'][0]['title'], "Test")
    
    def test_extract_json_from_plain(self):
        """Test JSON extraction from plain JSON."""
        content = '{"skills": [{"title": "Test"}]}'
        result = self.service._extract_json(content)
        self.assertEqual(result['skills'][0]['title'], "Test")
    
    def test_extract_json_invalid(self):
        """Test JSON extraction with invalid JSON."""
        content = "This is not JSON"
        result = self.service._extract_json(content)
        self.assertIsNone(result)
    
    @patch('skills.ai_tree_generator.lm_client.chat_completion')
    def test_call_lm_studio_success(self, mock_chat):
        """Test successful LM Studio call."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'skills': [
                            {
                                'title': 'Basics',
                                'description': 'Learn basics',
                                'category': 'Fundamentals',
                                'difficulty': 1,
                                'estimated_hours': 5,
                                'prerequisites': [],
                                'quest_titles': ['Quest 1', 'Quest 2']
                            }
                        ]
                    })
                }
            }]
        }
        mock_chat.return_value = mock_response
        
        result = self.service._call_lm_studio("Python", 2)
        
        self.assertIn('skills', result)
        self.assertEqual(len(result['skills']), 1)
        self.assertEqual(result['skills'][0]['title'], 'Basics')
    
    @patch('skills.ai_tree_generator.lm_client.chat_completion')
    def test_call_lm_studio_retry_on_invalid_json(self, mock_chat):
        """Test that LM Studio retries on invalid JSON."""
        # First call returns invalid JSON, second returns valid
        mock_chat.side_effect = [
            {
                'choices': [{
                    'message': {'content': 'Invalid JSON'}
                }]
            },
            {
                'choices': [{
                    'message': {
                        'content': json.dumps({
                            'skills': [{'title': 'Basics', 'description': 'Test', 'difficulty': 1, 'prerequisites': []}]
                        })
                    }
                }]
            }
        ]
        
        result = self.service._call_lm_studio("Python", 2)
        
        self.assertIn('skills', result)
        self.assertEqual(mock_chat.call_count, 2)
    
    @patch('skills.ai_tree_generator.lm_client.chat_completion')
    def test_process_skills_creates_skills(self, mock_chat):
        """Test that _process_skills creates Skill instances."""
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="generating"
        )
        
        skills_data = [
            {
                'title': 'Variables',
                'description': 'Learn variables and data types.',
                'category': 'Basics',
                'difficulty': 1,
                'estimated_hours': 2,
                'prerequisites': [],
                'quest_titles': ['Quest 1', 'Quest 2']
            },
            {
                'title': 'Functions',
                'description': 'Learn function definition and calls.',
                'category': 'Basics',
                'difficulty': 2,
                'estimated_hours': 3,
                'prerequisites': ['Variables'],
                'quest_titles': ['Quest 1', 'Quest 2']
            }
        ]
        
        count, errors = self.service._process_skills(str(tree.id), skills_data, "Python")
        
        self.assertEqual(count, 2)
        self.assertEqual(len(errors), 0)
        
        # Check skills were created
        self.assertEqual(Skill.objects.filter(category='custom_python').count(), 2)
        
        # Check prerequisite was created
        variables_skill = Skill.objects.get(title='Variables')
        functions_skill = Skill.objects.get(title='Functions')
        
        prereq = SkillPrerequisite.objects.get(
            from_skill=variables_skill,
            to_skill=functions_skill
        )
        self.assertIsNotNone(prereq)
        
        # Check quests were created
        self.assertEqual(Quest.objects.filter(skill=variables_skill).count(), 2)
        self.assertEqual(Quest.objects.filter(skill=functions_skill).count(), 2)
    
    @patch('skills.ai_tree_generator.lm_client.chat_completion')
    def test_process_skills_handles_missing_prerequisites(self, mock_chat):
        """Test that _process_skills handles missing prerequisites gracefully."""
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="generating"
        )
        
        skills_data = [
            {
                'title': 'Advanced',
                'description': 'Advanced topic.',
                'category': 'Advanced',
                'difficulty': 4,
                'estimated_hours': 5,
                'prerequisites': ['NonExistent'],
                'quest_titles': ['Quest 1', 'Quest 2']
            }
        ]
        
        count, errors = self.service._process_skills(str(tree.id), skills_data, "Python")
        
        self.assertEqual(count, 1)
        # Should have warning about missing prerequisite
        self.assertTrue(any('NonExistent' in str(e) for e in errors))
    
    @patch('skills.ai_tree_generator.lm_client.chat_completion')
    def test_execute_generation_full_pipeline(self, mock_chat):
        """Test full generation pipeline."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'skills': [
                            {
                                'title': 'Basics',
                                'description': 'Learn basics of the topic.',
                                'category': 'Fundamentals',
                                'difficulty': 1,
                                'estimated_hours': 5,
                                'prerequisites': [],
                                'quest_titles': ['Quest 1', 'Quest 2']
                            }
                        ]
                    })
                }
            }]
        }
        mock_chat.return_value = mock_response
        
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="generating"
        )
        
        result = self.service.execute_generation(str(tree.id), "Python", 2)
        
        self.assertEqual(result['status'], 'ready')
        self.assertEqual(result['skill_count'], 1)
        
        # Verify tree status updated
        tree.refresh_from_db()
        self.assertEqual(tree.status, 'ready')
        self.assertEqual(tree.skills_created.count(), 1)


class GenerateSkillTreeAPITests(APITestCase):
    """Test API endpoints for skill tree generation."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
    
    @patch('skills.ai_tree_generator.SkillTreeGeneratorService.generate_tree')
    def test_generate_tree_endpoint(self, mock_generate):
        """Test POST /api/skills/generate/ endpoint."""
        mock_generate.return_value = {
            'tree_id': '550e8400-e29b-41d4-a716-446655440000',
            'status': 'generating',
            'topic': 'Python'
        }
        
        response = self.client.post('/api/skills/generate/', {
            'topic': 'Python',
            'depth': 3
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data['status'], 'generating')
    
    def test_generate_tree_requires_topic(self):
        """Test that topic is required."""
        response = self.client.post('/api/skills/generate/', {
            'depth': 3
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_list_generated_trees(self):
        """Test GET /api/skills/generated/ endpoint."""
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="ready"
        )
        
        response = self.client.get('/api/skills/generated/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['topic'], 'Python')
    
    def test_get_tree_detail(self):
        """Test GET /api/skills/generated/{tree_id}/ endpoint."""
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="ready"
        )
        
        response = self.client.get(f'/api/skills/generated/{tree.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['topic'], 'Python')
    
    def test_get_tree_detail_not_found(self):
        """Test 404 for non-existent tree."""
        response = self.client.get('/api/skills/generated/550e8400-e29b-41d4-a716-446655440000/')
        
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_get_tree_detail_forbidden_for_private_tree(self):
        """Test that private trees are not accessible to other users."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=other_user,
            status="ready",
            is_public=False
        )
        
        response = self.client.get(f'/api/skills/generated/{tree.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_get_tree_detail_allowed_for_public_tree(self):
        """Test that public trees are accessible to all users."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=other_user,
            status="ready",
            is_public=True
        )
        
        response = self.client.get(f'/api/skills/generated/{tree.id}/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_publish_tree_requires_staff(self):
        """Test that only staff can publish trees."""
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="ready"
        )
        
        response = self.client.post(f'/api/skills/generated/{tree.id}/publish/')
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_publish_tree_staff_only(self):
        """Test that staff can publish trees."""
        self.user.is_staff = True
        self.user.save()
        
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="ready"
        )
        
        response = self.client.post(f'/api/skills/generated/{tree.id}/publish/')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        tree.refresh_from_db()
        self.assertTrue(tree.is_public)
    
    def test_publish_tree_requires_ready_status(self):
        """Test that only ready trees can be published."""
        self.user.is_staff = True
        self.user.save()
        
        tree = GeneratedSkillTree.objects.create(
            topic="Python",
            created_by=self.user,
            status="generating"
        )
        
        response = self.client.post(f'/api/skills/generated/{tree.id}/publish/')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class SkillTreeGeneratorIntegrationTests(TestCase):
    """Integration tests for the full generation pipeline."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    @patch('skills.ai_tree_generator.lm_client.chat_completion')
    def test_full_generation_pipeline(self, mock_chat):
        """Test complete generation pipeline from API to database."""
        mock_response = {
            'choices': [{
                'message': {
                    'content': json.dumps({
                        'skills': [
                            {
                                'title': 'Python Basics',
                                'description': 'Learn Python fundamentals and syntax.',
                                'category': 'Programming',
                                'difficulty': 1,
                                'estimated_hours': 10,
                                'prerequisites': [],
                                'quest_titles': ['Hello World', 'Variables']
                            },
                            {
                                'title': 'Functions',
                                'description': 'Master function definition and scope.',
                                'category': 'Programming',
                                'difficulty': 2,
                                'estimated_hours': 8,
                                'prerequisites': ['Python Basics'],
                                'quest_titles': ['Define Functions', 'Recursion']
                            }
                        ]
                    })
                }
            }]
        }
        mock_chat.return_value = mock_response
        
        service = SkillTreeGeneratorService()
        
        # Generate tree
        result = service.generate_tree("Python", self.user, 2)
        tree_id = result['tree_id']
        
        # Execute generation
        exec_result = service.execute_generation(tree_id, "Python", 2)
        
        self.assertEqual(exec_result['status'], 'ready')
        self.assertEqual(exec_result['skill_count'], 2)
        
        # Verify database state
        tree = GeneratedSkillTree.objects.get(id=tree_id)
        self.assertEqual(tree.status, 'ready')
        self.assertEqual(tree.skills_created.count(), 2)
        
        # Verify skills
        basics = Skill.objects.get(title='Python Basics')
        functions = Skill.objects.get(title='Functions')
        
        self.assertEqual(basics.difficulty, 1)
        self.assertEqual(functions.difficulty, 2)
        
        # Verify prerequisite
        prereq = SkillPrerequisite.objects.get(
            from_skill=basics,
            to_skill=functions
        )
        self.assertIsNotNone(prereq)
        
        # Verify quests
        self.assertEqual(Quest.objects.filter(skill=basics).count(), 2)
        self.assertEqual(Quest.objects.filter(skill=functions).count(), 2)
    
    def test_circular_dependency_detection(self):
        """Test that circular dependencies are detected and skipped."""
        service = SkillTreeGeneratorService()
        
        # Create skills manually
        skill_a = Skill.objects.create(
            title='Skill A',
            description='Test skill A',
            category='custom_test',
            difficulty=1
        )
        skill_b = Skill.objects.create(
            title='Skill B',
            description='Test skill B',
            category='custom_test',
            difficulty=1
        )
        skill_c = Skill.objects.create(
            title='Skill C',
            description='Test skill C',
            category='custom_test',
            difficulty=1
        )
        
        # Create a chain: A -> B -> C
        SkillPrerequisite.objects.create(from_skill=skill_a, to_skill=skill_b)
        SkillPrerequisite.objects.create(from_skill=skill_b, to_skill=skill_c)
        
        # Try to create a cycle: C -> A (would create A -> B -> C -> A)
        would_cycle = service._would_create_cycle(skill_c, skill_a)
        self.assertTrue(would_cycle, "Should detect cycle: C -> A when A -> B -> C exists")
        
        # Try to create a non-cycle: C -> A (no path from A back to C)
        would_cycle = service._would_create_cycle(skill_a, skill_c)
        self.assertFalse(would_cycle, "Should not detect cycle: A -> C when A -> B -> C exists")
    
    def test_dynamic_category_support(self):
        """Test that dynamic categories are supported for generated skills."""
        # Create a skill with dynamic category
        skill = Skill.objects.create(
            title='Machine Learning Basics',
            description='Learn ML fundamentals',
            category='custom_machine_learning',  # Dynamic category
            difficulty=2
        )
        
        self.assertEqual(skill.category, 'custom_machine_learning')
        self.assertIn('custom_', skill.category)
    
    def test_skill_visibility_filtering(self):
        """Test that unpublished generated skills are not visible to other users."""
        other_user = User.objects.create_user(
            username='otheruser',
            email='other@example.com',
            password='testpass123'
        )
        
        # Create an unpublished tree with skills
        tree = GeneratedSkillTree.objects.create(
            topic='Python',
            created_by=other_user,
            status='ready',
            is_public=False
        )
        
        skill = Skill.objects.create(
            title='Unpublished Skill',
            description='This skill is unpublished',
            category='custom_python',
            difficulty=1
        )
        tree.skills_created.add(skill)
        
        # Create a published tree with skills
        published_tree = GeneratedSkillTree.objects.create(
            topic='JavaScript',
            created_by=other_user,
            status='ready',
            is_public=True
        )
        
        published_skill = Skill.objects.create(
            title='Published Skill',
            description='This skill is published',
            category='custom_javascript',
            difficulty=1
        )
        published_tree.skills_created.add(published_skill)
        
        # Create a non-generated skill (always visible)
        base_skill = Skill.objects.create(
            title='Base Skill',
            description='This is a base skill',
            category='algorithms',
            difficulty=1
        )
        
        # Authenticate as current user and get tree
        client = Client()
        client.force_login(self.user)
        response = client.get('/api/skills/')
        
        # Parse response
        import json
        data = json.loads(response.content)
        skill_titles = [node['name'] for node in data['nodes']]
        
        # Unpublished skill should NOT be visible
        self.assertNotIn('Unpublished Skill', skill_titles)
        
        # Published skill SHOULD be visible
        self.assertIn('Published Skill', skill_titles)
        
        # Base skill SHOULD be visible
        self.assertIn('Base Skill', skill_titles)
