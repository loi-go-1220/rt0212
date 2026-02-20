from django.contrib import admin
from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'get_username', 'get_email']
    search_fields = ['user__username', 'user__email']
    
    def get_username(self, obj):
        return obj.user.username
    get_username.short_description = 'Username'
    
    def get_email(self, obj):
        return obj.user.email
    get_email.short_description = 'Email'
