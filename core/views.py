from django.shortcuts import render
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache     

# The order matters!
@login_required
@never_cache                          
def dashboard(request):
    return render(request, 'core/dashboard.html')