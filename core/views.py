from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache 
from .models import UserSkill
from .utils import calculate_radar_stats    
from django.shortcuts import redirect

def index_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/auth/register/?mode=login')

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

