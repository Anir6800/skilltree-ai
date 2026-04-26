from django.contrib import admin
from .models import AdminContent, AssessmentQuestion

@admin.register(AdminContent)
class AdminContentAdmin(admin.ModelAdmin):
    list_display = ['title', 'skill', 'content_type', 'status', 'created_by', 'created_at']
    list_filter = ['status', 'content_type', 'skill__category']
    search_fields = ['title', 'body']

@admin.register(AssessmentQuestion)
class AssessmentQuestionAdmin(admin.ModelAdmin):
    list_display = ['quest', 'question_type', 'points', 'created_at']
    list_filter = ['question_type', 'quest__skill']
    search_fields = ['prompt']
