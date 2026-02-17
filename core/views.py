from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache 
from .models import UserSkill    

# The order matters!
@login_required
@never_cache                          
def dashboard(request):
    user_skills = UserSkill.objects.filter(user=request.user)
    
    context = {
        'skills': user_skills,  # This MUST match the name in your template {% for user_skill in skills %}
    }
    return render(request, 'core/dashboard.html',context)