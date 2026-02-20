from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm, PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from .forms import UserRegisterForm, UserUpdateForm, ProfileUpdateForm


def register(request):
    """User registration view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            username = form.cleaned_data.get('username')
            messages.success(request, f'Account created for {username}! You can now log in.')
            return redirect('login')
    else:
        form = UserRegisterForm()
    
    return render(request, 'accounts/register.html', {'form': form})


def user_login(request):
    """User login view"""
    if request.user.is_authenticated:
        return redirect('dashboard')
    
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.success(request, f'Welcome back, {username}!')
                next_page = request.GET.get('next', 'dashboard')
                return redirect(next_page)
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    else:
        form = AuthenticationForm()
    
    return render(request, 'accounts/login.html', {'form': form})


@login_required
def user_logout(request):
    """User logout view"""
    logout(request)
    messages.success(request, 'You have been logged out successfully.')
    return redirect('login')


@login_required
def profile_settings(request):
    """User profile settings view"""
    from django.contrib.auth import update_session_auth_hash # Local import needed

    if request.method == 'POST':
        # Determine which form was submitted
        if 'update_profile' in request.POST:
            # Update user account information only
            u_form = UserUpdateForm(request.POST, instance=request.user)
            p_form = ProfileUpdateForm(instance=request.user.profile)  # Initialize empty form
            pwd_form = PasswordChangeForm(request.user)  # Initialize empty form
            
            if u_form.is_valid():
                u_form.save()
                messages.success(request, 'Your account information has been updated!')
                return redirect('profile_settings')
        
        elif 'update_defaults' in request.POST:
            # Update default name and base resume
            u_form = UserUpdateForm(instance=request.user)  # Initialize empty form
            p_form = ProfileUpdateForm(request.POST, instance=request.user.profile)
            pwd_form = PasswordChangeForm(request.user)  # Initialize empty form
            
            if p_form.is_valid():
                p_form.save()
                messages.success(request, 'Your default settings have been updated!')
                return redirect('profile_settings')
        
        elif 'change_password' in request.POST:
            u_form = UserUpdateForm(instance=request.user)  # Initialize empty form
            p_form = ProfileUpdateForm(instance=request.user.profile)  # Initialize empty form
            pwd_form = PasswordChangeForm(request.user, request.POST)
            
            if pwd_form.is_valid():
                user = pwd_form.save()
                update_session_auth_hash(request, user)  # Keep user logged in
                messages.success(request, 'Your password has been changed!')
                return redirect('profile_settings')
        else:
            # Default: show all forms empty
            u_form = UserUpdateForm(instance=request.user)
            p_form = ProfileUpdateForm(instance=request.user.profile)
            pwd_form = PasswordChangeForm(request.user)
    else:
        # GET request: show all forms
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)
        pwd_form = PasswordChangeForm(request.user)
    
    context = {
        'u_form': u_form,
        'p_form': p_form,
        'pwd_form': pwd_form,
    }
    
    return render(request, 'accounts/settings.html', context)
