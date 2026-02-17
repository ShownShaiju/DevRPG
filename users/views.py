from django.shortcuts import render, redirect
from django.contrib.auth.models import User
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from .models import Profile

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
   print("logout_view called")

