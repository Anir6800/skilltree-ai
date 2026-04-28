"""
Seed data: Badge definitions for SkillTree AI.
Run via: python manage.py seed_badges
Or called from the seed_all management command.
"""

BADGE_SEED_DATA = [
    # ── XP Milestones ────────────────────────────────────────────────────────
    {
        "slug": "first-xp",
        "name": "First Steps",
        "description": "Earned your first XP on SkillTree AI.",
        "icon_emoji": "🌱",
        "rarity": "common",
        "unlock_condition": {"event_type": "xp_gained", "criteria": {"min_total_xp": 1}},
    },
    {
        "slug": "xp-500",
        "name": "Rising Coder",
        "description": "Reached 500 total XP.",
        "icon_emoji": "⚡",
        "rarity": "common",
        "unlock_condition": {"event_type": "xp_gained", "criteria": {"min_total_xp": 500}},
    },
    {
        "slug": "xp-1000",
        "name": "Code Warrior",
        "description": "Reached 1,000 total XP.",
        "icon_emoji": "🗡️",
        "rarity": "rare",
        "unlock_condition": {"event_type": "xp_gained", "criteria": {"min_total_xp": 1000}},
    },
    {
        "slug": "xp-5000",
        "name": "Elite Developer",
        "description": "Reached 5,000 total XP.",
        "icon_emoji": "💎",
        "rarity": "epic",
        "unlock_condition": {"event_type": "xp_gained", "criteria": {"min_total_xp": 5000}},
    },
    {
        "slug": "xp-10000",
        "name": "Legendary Coder",
        "description": "Reached 10,000 total XP. You are a legend.",
        "icon_emoji": "🏆",
        "rarity": "legendary",
        "unlock_condition": {"event_type": "xp_gained", "criteria": {"min_total_xp": 10000}},
    },
    # ── Quest Completions ────────────────────────────────────────────────────
    {
        "slug": "first-quest",
        "name": "Quest Starter",
        "description": "Completed your first quest.",
        "icon_emoji": "🎯",
        "rarity": "common",
        "unlock_condition": {"event_type": "quest_passed", "criteria": {"min_quests_passed": 1}},
    },
    {
        "slug": "quests-10",
        "name": "Quest Hunter",
        "description": "Completed 10 quests.",
        "icon_emoji": "🏹",
        "rarity": "common",
        "unlock_condition": {"event_type": "quest_passed", "criteria": {"min_quests_passed": 10}},
    },
    {
        "slug": "quests-50",
        "name": "Quest Master",
        "description": "Completed 50 quests.",
        "icon_emoji": "🌟",
        "rarity": "rare",
        "unlock_condition": {"event_type": "quest_passed", "criteria": {"min_quests_passed": 50}},
    },
    {
        "slug": "quests-100",
        "name": "Century Coder",
        "description": "Completed 100 quests.",
        "icon_emoji": "💯",
        "rarity": "epic",
        "unlock_condition": {"event_type": "quest_passed", "criteria": {"min_quests_passed": 100}},
    },
    # ── Streaks ──────────────────────────────────────────────────────────────
    {
        "slug": "streak-3",
        "name": "On a Roll",
        "description": "Maintained a 3-day learning streak.",
        "icon_emoji": "🔥",
        "rarity": "common",
        "unlock_condition": {"event_type": "streak_updated", "criteria": {"min_streak_days": 3}},
    },
    {
        "slug": "streak-7",
        "name": "Week Warrior",
        "description": "Maintained a 7-day learning streak.",
        "icon_emoji": "🔥🔥",
        "rarity": "rare",
        "unlock_condition": {"event_type": "streak_updated", "criteria": {"min_streak_days": 7}},
    },
    {
        "slug": "streak-30",
        "name": "Unstoppable",
        "description": "Maintained a 30-day learning streak.",
        "icon_emoji": "🌋",
        "rarity": "epic",
        "unlock_condition": {"event_type": "streak_updated", "criteria": {"min_streak_days": 30}},
    },
    # ── Skills ───────────────────────────────────────────────────────────────
    {
        "slug": "first-skill",
        "name": "Skill Unlocked",
        "description": "Completed your first skill.",
        "icon_emoji": "🔓",
        "rarity": "common",
        "unlock_condition": {"event_type": "skill_completed", "criteria": {"min_skills_completed": 1}},
    },
    {
        "slug": "skills-5",
        "name": "Skill Collector",
        "description": "Completed 5 skills.",
        "icon_emoji": "📚",
        "rarity": "rare",
        "unlock_condition": {"event_type": "skill_completed", "criteria": {"min_skills_completed": 5}},
    },
    # ── Multiplayer ──────────────────────────────────────────────────────────
    {
        "slug": "first-arena-win",
        "name": "Arena Victor",
        "description": "Won your first multiplayer arena match.",
        "icon_emoji": "⚔️",
        "rarity": "rare",
        "unlock_condition": {"event_type": "match_won", "criteria": {"min_wins": 1}},
    },
    {
        "slug": "arena-wins-10",
        "name": "Arena Champion",
        "description": "Won 10 multiplayer arena matches.",
        "icon_emoji": "👑",
        "rarity": "epic",
        "unlock_condition": {"event_type": "match_won", "criteria": {"min_wins": 10}},
    },
    # ── Social ───────────────────────────────────────────────────────────────
    {
        "slug": "first-share",
        "name": "Open Source Spirit",
        "description": "Shared your first solution with the community.",
        "icon_emoji": "🤝",
        "rarity": "common",
        "unlock_condition": {"event_type": "solution_shared", "criteria": {"min_shares": 1}},
    },
    {
        "slug": "study-group-joined",
        "name": "Team Player",
        "description": "Joined a study group.",
        "icon_emoji": "👥",
        "rarity": "common",
        "unlock_condition": {"event_type": "group_joined", "criteria": {}},
    },
]


def run(apps=None, schema_editor=None):
    """
    Seed badge definitions. Safe to run multiple times (uses get_or_create).
    Can be called from a migration RunPython or the seed_all command.
    """
    if apps is not None:
        Badge = apps.get_model('users', 'Badge')
    else:
        from users.models import Badge

    created_count = 0
    for data in BADGE_SEED_DATA:
        slug = data.pop('slug')
        _, created = Badge.objects.get_or_create(slug=slug, defaults=data)
        data['slug'] = slug  # restore for idempotency
        if created:
            created_count += 1

    print(f"✅ Badges seeded: {created_count} new, {len(BADGE_SEED_DATA) - created_count} already existed.")
