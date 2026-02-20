from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache 
from .models import UserSkill
from .utils import calculate_radar_stats    

# The order matters!
@login_required
@never_cache                          
def dashboard(request):
    user_skills = UserSkill.objects.filter(user=request.user)
    radar_data = calculate_radar_stats(user_skills)
    
    
    context = {
        'skills': user_skills,
        'stats': radar_data['stats'],
        'polygon_points': radar_data['polygon_points'],
    }
    return render(request, 'core/dashboard.html',context)