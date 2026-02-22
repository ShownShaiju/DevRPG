from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import Profile
from django.urls import reverse
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from .forms import UserUpdateForm, ProfileUpdateForm, AddSkillForm
from django.contrib.auth.decorators import login_required
from core.models import UserSkill, Skill
from .tasks import optimize_avatar


def register(request):
    if request.method == "POST":
        # Get data directly from the HTML inputs
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        confirm_password = request.POST['confirm-password']

        # 1. Validation
        if password != confirm_password:
            messages.error(request, "Passwords do not match!")
            return redirect('register')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already taken!")
            return redirect('register')

        if User.objects.filter(email=email).exists():
            messages.error(request, "Email already registered!")
            return redirect('register')

        try:
            # Check the password against all settings.py rules
            # We pass a temporary User object so it can check for similarity (username vs password)
            validate_password(password, user=User(username=username, email=email))
            
        except ValidationError as e:
            # If any rule is broken, it throws an error with a list of messages
            for error in e.messages:
                messages.error(request, error)
            return redirect('register')
        
        
        # 2. Create User
        user = User.objects.create_user(username=username, email=email, password=password)
        user.first_name = username # Default first name to username
        user.save()

        # 3. Create RPG Profile (Important!)
        profile = Profile.objects.create(user=user)
        profile.job_title = "Novice Developer" # Default Class
        profile.save()

        # 4. Log them in immediately and go to Dashboard
        login(request, user)
        messages.success(request, "Welcome to the Guild!")
        return redirect('dashboard')

    return render(request, 'users/register.html')




def login_view(request):
    if request.method == "POST":
        email = request.POST['email'] # We are using the 'email' input as the login ID
        password = request.POST['password']
        
        # Check if a user with this email exists
        try:
            user_obj = User.objects.get(email=email)
            username = user_obj.username # Get their actual username
        except User.DoesNotExist:
            messages.error(request, "No hero found with that email.")
            return redirect('register') # Or login, but we are using the same page

        user = authenticate(request, username=username, password=password)
        
        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Invalid credentials.")
    
    return render(request, 'users/register.html') # Render the same page
# users/views.py

def logout_view(request):
    # 1. Clear the session data (logs the user out)
    logout(request)
    
    # 2. Add a message (Your HTML toast logic will pick this up!)
    messages.info(request, "You have been logged out.")
    
    # 3. Redirect to register page with the 'mode=login' query parameter
    # We use reverse() to get the URL for 'register', then append the query param.
    return redirect(f"{reverse('register')}?mode=login")

@login_required
def profile_edit(request):
    if request.method == 'POST':
        u_form = UserUpdateForm(request.POST, instance=request.user)
        p_form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)

        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            profile = p_form.save() # Capture the saved profile instance
            
            # offload the image processing to Celery ONLY if a new file was uploaded
            if 'avatar_image' in request.FILES:
                optimize_avatar.delay(profile.id) 
                # .delay() is the critical method. It sends the task to Redis.

            messages.success(request, 'Your profile attributes have been updated!')
            return redirect('dashboard') 

    else:
        u_form = UserUpdateForm(instance=request.user)
        p_form = ProfileUpdateForm(instance=request.user.profile)

    context = {
        'u_form': u_form,
        'p_form': p_form
    }

    return render(request, 'users/profile_edit.html', context)
@login_required
def skill_manager(request):
    user_skills = UserSkill.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = AddSkillForm(request.POST)
        if form.is_valid():
            skill_instance = form.save(commit=False)
            skill_instance.user = request.user
            skill_instance.save()
            return redirect('skill_manager')
    else:
        form = AddSkillForm()
        
    return render(request, 'users/skill_manager.html', {
        'user_skills': user_skills,
        'form': form
    })

@login_required
def delete_skill(request, pk):
    skill = get_object_or_404(UserSkill, pk=pk, user=request.user)
    skill.delete()
    return redirect('skill_manager')