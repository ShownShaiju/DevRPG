from django import forms
from django.contrib.auth.models import User
from .models import Profile

# 1. Update User Data (Exclude Email as requested)
class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'last_name'] # Email removed!

# 2. Update Profile Data
class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        # We use 'avatar_url' because that is what is in your models.py right now
        fields = ['avatar_image', 'job_title', 'bio', 'location']