from django.contrib import admin
from .models import Resume, InterviewQuestionAnswer


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ['profile_name', 'target_company', 'job_title', 'user', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'target_company']
    search_fields = ['profile_name', 'target_company', 'job_title', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'profile_name')
        }),
        ('Job Information', {
            'fields': ('target_company', 'job_title', 'job_url', 'job_description')
        }),
        ('Resume Content', {
            'fields': ('initial_resume_text', 'tailored_resume_text')
        }),
        ('Status', {
            'fields': ('status', 'error_message')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(InterviewQuestionAnswer)
class InterviewQuestionAnswerAdmin(admin.ModelAdmin):
    list_display = ['get_resume_info', 'get_question_preview', 'created_at']
    list_filter = ['created_at', 'resume__target_company', 'resume__user']
    search_fields = ['question', 'answer', 'resume__profile_name', 'resume__target_company']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Resume Information', {
            'fields': ('resume',)
        }),
        ('Question & Answer', {
            'fields': ('question', 'answer')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_resume_info(self, obj):
        return f"{obj.resume.profile_name} - {obj.resume.target_company}"
    get_resume_info.short_description = 'Resume'
    get_resume_info.admin_order_field = 'resume__profile_name'
    
    def get_question_preview(self, obj):
        return obj.question[:100] + "..." if len(obj.question) > 100 else obj.question
    get_question_preview.short_description = 'Question Preview'
    get_question_preview.admin_order_field = 'question'
