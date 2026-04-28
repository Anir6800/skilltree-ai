from django.apps import AppConfig


class AiEvaluationConfig(AppConfig):
    name = 'ai_evaluation'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        """Register signal handlers when app is ready."""
        import ai_evaluation.quote_signals
