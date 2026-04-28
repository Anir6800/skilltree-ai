from django.apps import AppConfig


class SkillsConfig(AppConfig):
    name = 'skills'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Register signal handlers when app is ready."""
        import skills.adaptive_signals
