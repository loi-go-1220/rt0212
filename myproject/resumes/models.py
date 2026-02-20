from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Resume(models.Model):
    """
    Resume model for storing job application and tailored resume data
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    # Relationships
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='resumes')
    
    # Input fields
    profile_name = models.CharField(
        max_length=200,
        help_text="User's name for this application"
    )
    target_company = models.CharField(max_length=200)
    job_title = models.CharField(max_length=200, blank=True, null=True)
    job_url = models.URLField(blank=True, null=True)
    job_description = models.TextField()
    initial_resume_text = models.TextField(help_text="Original resume content")
    
    # Output fields
    tailored_resume_text = models.TextField(
        blank=True,
        help_text="AI-generated tailored resume"
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    error_message = models.TextField(blank=True, null=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        verbose_name = "Resume"
        verbose_name_plural = "Resumes"
    
    def __str__(self):
        return f"{self.profile_name} - {self.target_company} ({self.job_title})"
    
    @property
    def is_completed(self):
        """Check if resume generation is completed"""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Check if resume generation is pending"""
        return self.status == 'pending'
    
    @property
    def is_failed(self):
        """Check if resume generation failed"""
        return self.status == 'failed'
