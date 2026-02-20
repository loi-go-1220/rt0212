from django import forms
from .models import Resume


class ResumeBuilderForm(forms.ModelForm):
    """
    Form for building/creating a new tailored resume
    """
    class Meta:
        model = Resume
        fields = [
            'profile_name',
            'target_company',
            'job_url',
            'job_description',
            'initial_resume_text'
        ]
        widgets = {
            'profile_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Your full name'
            }),
            'target_company': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Google, Microsoft, etc.'
            }),
            'job_url': forms.URLInput(attrs={
                'class': 'form-control',
                'placeholder': 'https://example.com/job-posting (optional)'
            }),
            'job_description': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 8,
                'placeholder': 'Paste the full job description here...'
            }),
            'initial_resume_text': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Paste your base resume here...'
            }),
        }
        labels = {
            'profile_name': 'Your Name',
            'target_company': 'Company Name',
            'job_url': 'Job URL',
            'job_description': 'Job Description',
            'initial_resume_text': 'Your Base Resume',
        }


class ResumeSearchForm(forms.Form):
    """
    Form for searching/filtering resume history
    """
    search = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Search by company name...'
        })
    )
    status = forms.ChoiceField(
        required=False,
        choices=[('', 'All Statuses')] + Resume.STATUS_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )
