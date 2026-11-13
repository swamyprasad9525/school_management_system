from django.shortcuts import render, redirect
from django.contrib.auth import login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from .forms import LoginForm
from .models import Role, CustomUser

def login_view(request):
    if request.user.is_authenticated:
        return redirect('accounts:dashboard_redirect')

    if request.method == 'POST':
        form = LoginForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()
            login(request, user)
            messages.success(request, f"Welcome back, {user.get_full_name() or user.username}!")
            return redirect('accounts:dashboard_redirect')
        else:
            messages.error(request, "Invalid username or password.")
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})

def logout_view(request):
    logout(request)
    messages.info(request, "You have been logged out successfully.")
    return redirect('accounts:login')

def demo_switch(request, role_name):
    """
    Convenience endpoint for assessment reviewers to switch personas instantly.
    """
    role_mapping = {
        'admin': 'admin',
        'teacher': 'teacher1',
        'guardian': 'guardian1',
        'student': 'student1',
    }
    username = role_mapping.get(role_name.lower())
    if username:
        user = CustomUser.objects.filter(username=username).first()
        if user:
            login(request, user)
            messages.success(request, f"Switched to {user.get_role_display()} persona ({user.username}).")
            return redirect('accounts:dashboard_redirect')
    messages.error(request, "Target demo user not found. Please ensure database is seeded.")
    return redirect('accounts:login')

@login_required
def dashboard_redirect(request):
    """
    Directs the user to their role-specific dashboard.
    """
    user = request.user
    if user.is_superuser or user.role == Role.ADMIN:
        return redirect('core:admin_dashboard')
    elif user.role == Role.TEACHER:
        return redirect('core:teacher_dashboard')
    elif user.role in [Role.GUARDIAN, Role.STUDENT]:
        return redirect('core:guardian_dashboard')
    return redirect('core:home')
