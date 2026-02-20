from django.contrib import admin
from .models import Resume


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
