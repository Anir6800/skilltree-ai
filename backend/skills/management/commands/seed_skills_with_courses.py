"""
seed_skills_with_courses — SkillTree AI Management Command
============================================================
Performs a full system reset, reseeds pre-loaded skills, then fetches real
Coursera and Udemy course recommendations (via Apify) for every skill.

Usage:
    python manage.py seed_skills_with_courses --confirm
    python manage.py seed_skills_with_courses --confirm --no-input
    python manage.py seed_skills_with_courses --confirm --enrich-only  # skip reset, only add courses

SRP: This command orchestrates the pipeline; it delegates
     - DB reset    → full_reset management command
     - Seeding     → seed_all management command
     - Courses     → CourseFetcherService
"""

import logging

from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = (
        "Wipe the database, reseed pre-loaded skills + quests, then attach "
        "Coursera and Udemy course recommendations to every skill via Apify."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help="Required: confirms the destructive database wipe.",
        )
        parser.add_argument(
            "--no-input",
            action="store_true",
            help="Skip interactive confirmation prompts.",
        )
        parser.add_argument(
            "--enrich-only",
            action="store_true",
            help=(
                "Skip reset and seed steps — only fetch courses for existing skills. "
                "Useful when the DB is already seeded and you just need to add courses."
            ),
        )
        parser.add_argument(
            "--admin-email",
            default="admin@skilltree.ai",
            help="Admin account email to create after reset.",
        )
        parser.add_argument(
            "--admin-password",
            default="Admin1234!",
            help="Admin account password to create after reset.",
        )

    def handle(self, *args, **options):
        if not options["confirm"]:
            raise CommandError(
                "Refusing to run without --confirm. "
                "This command will WIPE the database and reseed it."
            )

        enrich_only = options["enrich_only"]

        if not enrich_only:
            self._step_reset(options)

        self._step_enrich_courses()
        self._print_summary()

    # ------------------------------------------------------------------
    # Pipeline steps
    # ------------------------------------------------------------------

    def _step_reset(self, options):
        """Wipe database, rerun migrations."""
        self.stdout.write(self.style.MIGRATE_HEADING("\n🗑️  Step 1/2 — Full database reset & seeding"))

        reset_kwargs = {
            "confirm": True,
            "no_input": True,
            "allow_production": False,
            # Use flush (preserve schema) instead of dropping the SQLite file.
            # Dropping requires exclusive access which fails when the dev server
            # is running and holds db.sqlite3 open.
            "skip_schema_rebuild": True,
            "skip_runtime_clean": True,   # don't nuke Redis during seeding
            "skip_redis_validation": True,
            "strict_runtime_validation": False,
            "skip_seed": False,           # Let full_reset seed everything so validation checks pass
            "with_demo_users": False,
            "admin_email": options["admin_email"],
            "admin_password": options["admin_password"],
            "verbosity": 1,
        }
        call_command("full_reset", **reset_kwargs)
        self.stdout.write(self.style.SUCCESS("  ✓ Database wiped, migrated and seeded"))

    def _step_enrich_courses(self):
        """Fetch courses for every skill that currently has none."""
        from django.conf import settings
        from skills.models import Skill
        from skills.course_fetcher import CourseFetcherService

        token = getattr(settings, "APIFY_API_TOKEN", "")
        if not token or token.startswith("apify_api_REPLACE"):
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  Step 2/2 — Course enrichment SKIPPED\n"
                    "   APIFY_API_TOKEN is not set in backend/.env.\n"
                    "   Add it and re-run with --enrich-only --confirm to fetch courses later."
                )
            )
            return

        skills = list(Skill.objects.all().order_by("category", "difficulty"))
        total = len(skills)
        self.stdout.write(
            self.style.MIGRATE_HEADING(
                f"\n🎓 Step 2/2 — Fetching courses for {total} skills (Coursera + Udemy via Apify)"
            )
        )

        fetcher = CourseFetcherService()
        success = 0
        failed = 0
        to_update = []

        for i, skill in enumerate(skills, 1):
            self.stdout.write(f"  [{i}/{total}] {skill.title} ...", ending="")
            try:
                courses = fetcher.fetch_courses_for_skill(skill.title, max_results=5)
                skill.courses = courses
                skill.save(update_fields=["courses", "updated_at"])
                self.stdout.write(
                    self.style.SUCCESS(f" {len(courses)} courses found")
                )
                success += 1
            except Exception as exc:
                self.stdout.write(self.style.ERROR(f" FAILED: {exc}"))
                failed += 1

        self.stdout.write(
            self.style.SUCCESS(
                f"\n  ✓ Courses attached: {success} skills enriched, {failed} failed"
            )
        )

    def _print_summary(self):
        from skills.models import Skill
        from quests.models import Quest

        skill_count = Skill.objects.count()
        skills_with_courses = Skill.objects.exclude(courses=[]).count()
        quest_count = Quest.objects.count()

        self.stdout.write(self.style.SUCCESS("\n✅ seed_skills_with_courses complete"))
        self.stdout.write(f"   Skills total:           {skill_count}")
        self.stdout.write(f"   Skills with courses:    {skills_with_courses}")
        self.stdout.write(f"   Quests total:           {quest_count}")
        self.stdout.write(
            "\nℹ️  Re-run with --enrich-only --confirm any time to refresh course data."
        )
