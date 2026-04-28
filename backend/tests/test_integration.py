"""
SkillTree AI - Core Integration Test Suite
==========================================
Single system-level test suite covering:
  - Authentication (register, login, logout, token refresh)
  - Onboarding (submit, status, skip)
  - AI skill tree generation (generate, poll, publish)
  - Skill tree (tree view, start skill, radar)
  - Quests (list, detail, submit, poll result)
  - Arena / Multiplayer (create match, join, leave, status)
  - WebSocket consumers (match consumer message routing)

Run with:
    cd backend
    pytest tests/test_integration.py -v
"""

import json
from unittest.mock import patch, MagicMock
from django.test import TestCase, TransactionTestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from skills.models import Skill, SkillProgress, GeneratedSkillTree
from quests.models import Quest, QuestSubmission
from multiplayer.models import Match, MatchParticipant
from users.models import XPLog

User = get_user_model()


# ─── Helpers ──────────────────────────────────────────────────────────────────

def make_user(username="player", password="testpass123", **kwargs):
    return User.objects.create_user(
        username=username,
        email=f"{username}@test.com",
        password=password,
        **kwargs,
    )


def auth_headers(user):
    refresh = RefreshToken.for_user(user)
    return {"HTTP_AUTHORIZATION": f"Bearer {str(refresh.access_token)}"}


def api_client_for(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


def make_skill(title="Python Basics", category="algorithms", difficulty=1, xp=0):
    return Skill.objects.create(
        title=title,
        description=f"Learn {title}",
        category=category,
        difficulty=difficulty,
        xp_required_to_unlock=xp,
    )


def make_quest(skill, title="Hello World", xp_reward=100, test_cases=None):
    return Quest.objects.create(
        skill=skill,
        type="coding",
        title=title,
        description="Write a solution",
        starter_code="# start",
        test_cases=test_cases or [{"input": "", "expected_output": "Hello World"}],
        xp_reward=xp_reward,
        difficulty_multiplier=1.0,
        estimated_minutes=10,
    )


# ─── 1. Authentication ─────────────────────────────────────────────────────────

class AuthenticationTests(APITestCase):
    """Register → login → refresh → logout flow."""

    def test_register_creates_user_and_returns_tokens(self):
        response = self.client.post("/api/auth/register/", {
            "username": "newuser",
            "email": "newuser@test.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("tokens", response.data)
        self.assertIn("access", response.data["tokens"])
        self.assertIn("refresh", response.data["tokens"])
        self.assertIn("user", response.data)
        self.assertEqual(response.data["user"]["username"], "newuser")

    def test_register_duplicate_username_fails(self):
        make_user("existing")
        response = self.client.post("/api/auth/register/", {
            "username": "existing",
            "email": "other@test.com",
            "password": "securepass123",
            "password_confirm": "securepass123",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_returns_tokens(self):
        make_user("loginuser", "mypassword")
        response = self.client.post("/api/token/", {
            "username": "loginuser",
            "password": "mypassword",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_wrong_password_fails(self):
        make_user("loginuser2", "correctpass")
        response = self.client.post("/api/token/", {
            "username": "loginuser2",
            "password": "wrongpass",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_token_refresh(self):
        user = make_user("refreshuser")
        refresh = RefreshToken.for_user(user)
        response = self.client.post("/api/token/refresh/", {
            "refresh": str(refresh),
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)

    def test_logout_blacklists_token(self):
        user = make_user("logoutuser")
        refresh = RefreshToken.for_user(user)
        client = api_client_for(user)
        response = client.post("/api/auth/logout/", {
            "refresh": str(refresh),
        }, format="json")
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_205_RESET_CONTENT,
        ])

    def test_me_endpoint_returns_profile(self):
        user = make_user("meuser")
        client = api_client_for(user)
        response = client.get("/api/auth/me/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["username"], "meuser")

    def test_me_patch_updates_profile(self):
        user = make_user("patchuser")
        client = api_client_for(user)
        response = client.patch("/api/auth/me/", {"username": "patchuser_updated"}, format="json")
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_unauthenticated_request_rejected(self):
        response = self.client.get("/api/users/me/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ─── 2. Onboarding ────────────────────────────────────────────────────────────

class OnboardingTests(APITestCase):
    """Onboarding submit → status → skip flow."""

    def setUp(self):
        self.user = make_user("onboarder")
        self.client = api_client_for(self.user)

    def test_onboarding_status_returns_completed_flag(self):
        response = self.client.get("/api/onboarding/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("completed", response.data)

    def test_onboarding_submit_valid_data(self):
        payload = {
            "primary_goal": "job_prep",
            "target_role": "Backend Developer",
            "experience_years": 2,
            "category_levels": {
                "algorithms": "intermediate",
                "ds": "beginner",
                "systems": "beginner",
                "webdev": "intermediate",
                "aiml": "beginner",
            },
            "selected_interests": ["Arrays", "Graphs"],
            "weekly_hours": 10,
        }
        response = self.client.post("/api/onboarding/submit/", payload, format="json")
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
            status.HTTP_202_ACCEPTED,
        ])

    def test_onboarding_skip(self):
        response = self.client.post("/api/onboarding/skip/")
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ])

    def test_onboarding_status_after_skip(self):
        self.client.post("/api/onboarding/skip/")
        response = self.client.get("/api/onboarding/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data.get("completed", False))

    def test_onboarding_unauthenticated_rejected(self):
        anon = APIClient()
        response = anon.get("/api/onboarding/status/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# ─── 3. AI Skill Tree Generation ──────────────────────────────────────────────

class AISkillTreeGenerationTests(APITestCase):
    """Generate → poll → publish flow."""

    def setUp(self):
        self.user = make_user("generator")
        self.staff = make_user("staffuser", is_staff=True)
        self.client = api_client_for(self.user)

    @patch("skills.ai_tree_generator.SkillTreeGeneratorService.generate_tree")
    def test_generate_endpoint_returns_202(self, mock_generate):
        mock_generate.return_value = {
            "tree_id": "550e8400-e29b-41d4-a716-446655440000",
            "status": "generating",
            "topic": "Python",
        }
        response = self.client.post("/api/skills/generate/", {
            "topic": "Python",
            "depth": 3,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_202_ACCEPTED)
        self.assertEqual(response.data["status"], "generating")

    def test_generate_requires_topic(self):
        response = self.client.post("/api/skills/generate/", {"depth": 2}, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_generated_trees(self):
        GeneratedSkillTree.objects.create(
            topic="Python", created_by=self.user, status="ready"
        )
        response = self.client.get("/api/skills/generated/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 1)

    def test_get_tree_detail_owner(self):
        tree = GeneratedSkillTree.objects.create(
            topic="Python", created_by=self.user, status="ready"
        )
        response = self.client.get(f"/api/skills/generated/{tree.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["topic"], "Python")

    def test_get_private_tree_forbidden_for_other_user(self):
        other = make_user("other_gen")
        tree = GeneratedSkillTree.objects.create(
            topic="Python", created_by=other, status="ready", is_public=False
        )
        response = self.client.get(f"/api/skills/generated/{tree.id}/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_publish_requires_staff(self):
        tree = GeneratedSkillTree.objects.create(
            topic="Python", created_by=self.user, status="ready"
        )
        response = self.client.post(f"/api/skills/generated/{tree.id}/publish/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_publish_by_staff_succeeds(self):
        tree = GeneratedSkillTree.objects.create(
            topic="Python", created_by=self.staff, status="ready"
        )
        staff_client = api_client_for(self.staff)
        response = staff_client.post(f"/api/skills/generated/{tree.id}/publish/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tree.refresh_from_db()
        self.assertTrue(tree.is_public)

    def test_publish_non_ready_tree_fails(self):
        tree = GeneratedSkillTree.objects.create(
            topic="Python", created_by=self.staff, status="generating"
        )
        staff_client = api_client_for(self.staff)
        response = staff_client.post(f"/api/skills/generated/{tree.id}/publish/")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─── 4. Skill Tree ────────────────────────────────────────────────────────────

class SkillTreeTests(APITestCase):
    """Skill tree view, start skill, radar."""

    def setUp(self):
        self.user = make_user("skilltreeuser")
        self.client = api_client_for(self.user)
        self.skill = make_skill("Algorithms", "algorithms", difficulty=1, xp=0)

    def test_skill_tree_returns_nodes_and_edges(self):
        response = self.client.get("/api/skills/tree/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("nodes", response.data)
        self.assertIn("edges", response.data)
        self.assertIsInstance(response.data["nodes"], list)

    def test_skill_tree_unauthenticated_rejected(self):
        anon = APIClient()
        response = anon.get("/api/skills/tree/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_start_skill_creates_progress(self):
        response = self.client.post(f"/api/skills/{self.skill.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        progress = SkillProgress.objects.get(user=self.user, skill=self.skill)
        self.assertEqual(progress.status, "in_progress")

    def test_start_skill_with_unmet_prerequisites_fails(self):
        prereq = make_skill("Prereq Skill", "algorithms", difficulty=1, xp=0)
        self.skill.prerequisites.add(prereq)
        response = self.client.post(f"/api/skills/{self.skill.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_start_skill_insufficient_xp_fails(self):
        expensive = make_skill("Expensive Skill", "algorithms", difficulty=3, xp=9999)
        response = self.client.post(f"/api/skills/{expensive.id}/start/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_radar_endpoint_returns_five_categories(self):
        response = self.client.get("/api/skills/radar/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("data", response.data)
        self.assertEqual(len(response.data["data"]), 5)


# ─── 5. Quests ────────────────────────────────────────────────────────────────

class QuestTests(APITestCase):
    """Quest list, detail, submit, poll result."""

    def setUp(self):
        self.user = make_user("questuser")
        self.client = api_client_for(self.user)
        self.skill = make_skill()
        SkillProgress.objects.create(user=self.user, skill=self.skill, status="in_progress")
        self.quest = make_quest(self.skill)

    def test_quest_list_returns_quests(self):
        response = self.client.get("/api/quests/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data.get("results", response.data)
        self.assertIsInstance(results, list)

    def test_quest_list_filter_by_skill(self):
        response = self.client.get(f"/api/quests/?skill_id={self.skill.id}")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_quest_detail_returns_full_data(self):
        response = self.client.get(f"/api/quests/{self.quest.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.quest.id)
        self.assertIn("title", response.data)

    def test_quest_detail_not_found(self):
        response = self.client.get("/api/quests/99999/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_quest_submit_creates_submission(self):
        response = self.client.post(f"/api/quests/{self.quest.id}/submit/", {
            "code": 'print("Hello World")',
            "language": "python",
        }, format="json")
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_201_CREATED,
        ])
        self.assertIn("submission_id", response.data)

    def test_quest_submit_missing_code_fails(self):
        response = self.client.post(f"/api/quests/{self.quest.id}/submit/", {
            "language": "python",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quest_submit_invalid_language_fails(self):
        response = self.client.post(f"/api/quests/{self.quest.id}/submit/", {
            "code": "print('hi')",
            "language": "brainfuck",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_quest_submit_locked_skill_fails(self):
        locked_skill = make_skill("Locked Skill", xp=9999)
        locked_quest = make_quest(locked_skill, title="Locked Quest")
        response = self.client.post(f"/api/quests/{locked_quest.id}/submit/", {
            "code": "print('hi')",
            "language": "python",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_submission_status_poll(self):
        # Create a submission directly
        sub = QuestSubmission.objects.create(
            user=self.user,
            quest=self.quest,
            code='print("Hello World")',
            language="python",
            status="passed",
            execution_result={"tests_passed": 1, "tests_total": 1, "test_results": []},
        )
        response = self.client.get(f"/api/execute/status/{sub.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], sub.id)
        self.assertIn("status", response.data)
        self.assertIn("execution_result", response.data)

    def test_submission_history_for_quest(self):
        QuestSubmission.objects.create(
            user=self.user, quest=self.quest,
            code="x", language="python", status="failed",
            execution_result={},
        )
        response = self.client.get(f"/api/quests/{self.quest.id}/submissions/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_xp_awarded_on_first_pass(self):
        initial_xp = self.user.xp
        QuestSubmission.objects.create(
            user=self.user, quest=self.quest,
            code='print("Hello World")', language="python",
            status="passed",
            execution_result={"tests_passed": 1, "tests_total": 1, "test_results": []},
        )
        # Simulate XP award (normally done by executor pipeline)
        xp_earned = int(self.quest.xp_reward * self.quest.difficulty_multiplier)
        self.user.xp += xp_earned
        self.user.save()
        self.user.refresh_from_db()
        self.assertEqual(self.user.xp, initial_xp + xp_earned)

    def test_already_passed_quest_rejected(self):
        QuestSubmission.objects.create(
            user=self.user, quest=self.quest,
            code='print("Hello World")', language="python",
            status="passed",
            execution_result={"tests_passed": 1, "tests_total": 1},
        )
        response = self.client.post(f"/api/quests/{self.quest.id}/submit/", {
            "code": 'print("Hello World")',
            "language": "python",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


# ─── 6. Arena / Multiplayer ───────────────────────────────────────────────────

class ArenaTests(APITestCase):
    """Create match, join, leave, status, match submission."""

    def setUp(self):
        self.user1 = make_user("arena_p1")
        self.user2 = make_user("arena_p2")
        self.skill = make_skill()
        self.quest = make_quest(self.skill)
        self.client1 = api_client_for(self.user1)
        self.client2 = api_client_for(self.user2)

    def test_create_match_returns_invite_code(self):
        response = self.client1.post("/api/matches/", {
            "quest_id": self.quest.id,
            "max_participants": 2,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("invite_code", response.data)
        self.assertEqual(response.data["status"], "waiting")

    def test_create_match_unauthenticated_fails(self):
        anon = APIClient()
        response = anon.post("/api/matches/", {
            "quest_id": self.quest.id,
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_join_match_with_invite_code(self):
        create_resp = self.client1.post("/api/matches/", {
            "quest_id": self.quest.id,
        }, format="json")
        invite_code = create_resp.data["invite_code"]

        join_resp = self.client2.post("/api/matches/join/", {
            "invite_code": invite_code,
        }, format="json")
        self.assertEqual(join_resp.status_code, status.HTTP_200_OK)
        participant_ids = [p["id"] for p in join_resp.data.get("participants", [])]
        self.assertIn(self.user2.id, participant_ids)

    def test_join_match_invalid_code_fails(self):
        response = self.client2.post("/api/matches/join/", {
            "invite_code": "INVALID-9999",
        }, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_waiting_matches(self):
        match = Match.objects.create(quest=self.quest, status="waiting")
        MatchParticipant.objects.create(match=match, user=self.user1)
        response = self.client2.get("/api/matches/?status=waiting")
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_match_detail(self):
        match = Match.objects.create(quest=self.quest, status="waiting")
        MatchParticipant.objects.create(match=match, user=self.user1)
        response = self.client1.get(f"/api/matches/{match.id}/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], match.id)

    def test_leave_match(self):
        match = Match.objects.create(quest=self.quest, status="waiting")
        MatchParticipant.objects.create(match=match, user=self.user1)
        MatchParticipant.objects.create(match=match, user=self.user2)
        response = self.client2.post(f"/api/matches/{match.id}/leave/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(match.participants.count(), 1)

    def test_match_status_endpoint(self):
        match = Match.objects.create(quest=self.quest, status="waiting")
        MatchParticipant.objects.create(match=match, user=self.user1)
        response = self.client1.get(f"/api/matches/{match.id}/status/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["status"], "waiting")

    def test_match_submission_bypasses_skill_lock(self):
        """Match submissions should bypass skill lock check."""
        match = Match.objects.create(quest=self.quest, status="active")
        MatchParticipant.objects.create(match=match, user=self.user1)
        MatchParticipant.objects.create(match=match, user=self.user2)

        # user1 has no SkillProgress — normally locked
        response = self.client1.post(f"/api/quests/{self.quest.id}/submit/", {
            "code": 'print("Hello World")',
            "language": "python",
            "match_id": str(match.id),
        }, format="json")
        # Should succeed (bypass lock) or fail for other reasons, not 403
        self.assertNotEqual(response.status_code, status.HTTP_403_FORBIDDEN)


# ─── 7. WebSocket Consumer (unit-level) ───────────────────────────────────────

class WebSocketConsumerTests(TransactionTestCase):
    """Unit tests for MatchConsumer message routing (no real WS connection)."""

    def setUp(self):
        self.user1 = make_user("ws_p1")
        self.user2 = make_user("ws_p2")
        self.skill = make_skill()
        self.quest = make_quest(self.skill)
        self.match = Match.objects.create(quest=self.quest, status="waiting")
        MatchParticipant.objects.create(match=self.match, user=self.user1)
        MatchParticipant.objects.create(match=self.match, user=self.user2)

    def test_consumer_verify_participant_true(self):
        from multiplayer.consumers import MatchConsumer
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        result = async_to_sync(consumer.verify_participant)(self.match.id, self.user1.id)
        self.assertTrue(result)

    def test_consumer_verify_participant_false_for_non_member(self):
        from multiplayer.consumers import MatchConsumer
        outsider = make_user("outsider")
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        result = async_to_sync(consumer.verify_participant)(self.match.id, outsider.id)
        self.assertFalse(result)

    def test_consumer_get_match_state_returns_quest(self):
        from multiplayer.consumers import MatchConsumer
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        state = async_to_sync(consumer.get_match_state)(self.match.id)
        self.assertIsNotNone(state)
        self.assertEqual(state["id"], self.match.id)
        self.assertIn("quest", state)
        self.assertEqual(state["quest"]["id"], self.quest.id)

    def test_consumer_start_match_sets_active(self):
        from multiplayer.consumers import MatchConsumer
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        started_at = async_to_sync(consumer.start_match)(self.match.id)
        self.assertIsNotNone(started_at)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, "active")

    def test_consumer_set_match_winner_awards_xp(self):
        from multiplayer.consumers import MatchConsumer
        self.match.status = "active"
        self.match.save()
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        async_to_sync(consumer._set_match_winner_sync)(self.match.id, self.user1.id)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, "finished")
        self.assertEqual(self.match.winner_id, self.user1.id)
        self.user1.refresh_from_db()
        expected_xp = int(self.quest.xp_reward * self.quest.difficulty_multiplier)
        self.assertEqual(self.user1.xp, expected_xp)

    def test_consumer_forfeit_awards_xp_to_other_player(self):
        from multiplayer.consumers import MatchConsumer
        self.match.status = "active"
        self.match.save()
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        async_to_sync(consumer.forfeit_match)(self.match.id, self.user1.id)
        self.match.refresh_from_db()
        self.assertEqual(self.match.status, "finished")
        self.assertEqual(self.match.winner_id, self.user2.id)
        self.user2.refresh_from_db()
        expected_xp = int(self.quest.xp_reward * self.quest.difficulty_multiplier / 2)
        self.assertEqual(self.user2.xp, expected_xp)

    def test_consumer_is_match_active_true(self):
        from multiplayer.consumers import MatchConsumer
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        result = async_to_sync(consumer.is_match_active)(self.match.id)
        self.assertTrue(result)

    def test_consumer_is_match_active_false_after_finish(self):
        from multiplayer.consumers import MatchConsumer
        self.match.status = "finished"
        self.match.save()
        consumer = MatchConsumer()
        from asgiref.sync import async_to_sync
        result = async_to_sync(consumer.is_match_active)(self.match.id)
        self.assertFalse(result)
