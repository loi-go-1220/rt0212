from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


DEFAULT_AI_PROMPT = """@base resume.md This is my sample resume
@jd.md is job description.
update this resume which align with jd even tech stack.
we should change tech stack (you should change content (language, framework, cloud platform...) which related with main tech stack in base resume to things (language, framework, cloud platform...) which related with job description's tech stacks )

Output requirements:
- Return ONLY the updated resume in Markdown.
- Keep it professional and ATS-friendly.
- Keep company names, titles, and dates as-is, but update wording/bullets to better match the JD.
- When the base resume mentions technologies that don't match the JD, replace them with the closest JD-related alternatives and adjust the bullet content accordingly (language, frameworks, cloud platform, tooling)."""


class UserProfile(models.Model):
    """
    Extended user profile with AI prompt customization and default resume data
    """
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    ai_prompt = models.TextField(
        default=DEFAULT_AI_PROMPT,
        help_text="Custom prompt for AI resume tailoring"
    )
    default_name = models.CharField(
        max_length=200,
        blank=True,
        help_text="Default name to use for resume applications"
    )
    default_base_resume = models.TextField(
        blank=True,
        help_text="Default base resume content in Markdown format"
    )
    
    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    class Meta:
        verbose_name = "User Profile"
        verbose_name_plural = "User Profiles"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    """Create a UserProfile when a new User is created"""
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    """Save the UserProfile when the User is saved"""
    instance.profile.save()
