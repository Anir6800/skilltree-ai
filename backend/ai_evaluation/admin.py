from django.contrib import admin
from .models import EvaluationResult


@admin.register(EvaluationResult)
class EvaluationResultAdmin(admin.ModelAdmin):
    list_display = ('submission_id', 'score', 'evaluated_at')
    search_fields = ('submission_id',)
