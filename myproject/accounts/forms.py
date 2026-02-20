from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import UserProfile


class UserRegisterForm(UserCreationForm):
    """
    User registration form
    """
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})


class UserUpdateForm(forms.ModelForm):
    """
    Form for updating user account information
    """
    email = forms.EmailField(widget=forms.EmailInput(attrs={'class': 'form-control'}))
    
    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }


class ProfileUpdateForm(forms.ModelForm):
    """
    Form for updating user profile
    Note: AI prompt is now built-in and cannot be customized
    """
    class Meta:
        model = UserProfile
        fields = ['default_name', 'default_base_resume']
        widgets = {
            'default_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Matthew Jin'
            }),
            'default_base_resume': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 12,
                'placeholder': 'Paste your default base resume here...'
            }),
        }
        labels = {
            'default_name': 'Default Name',
            'default_base_resume': 'Default Base Resume',
        }
        help_texts = {
            'default_name': 'This name will be automatically filled when creating new resumes',
            'default_base_resume': 'This resume content will be automatically loaded when creating new resumes',
        }
