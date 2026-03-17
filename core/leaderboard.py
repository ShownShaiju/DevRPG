from django.shortcuts import render
from django.contrib.auth.models import User
from guilds.models import Guild 

def set_leaderboard(request):

    top_players = User.objects.filter(
        is_superuser=False, 
        is_staff=False
    ).select_related('profile').order_by('-profile__level', '-profile__total_xp')[:50]
   
    top_guilds = Guild.objects.order_by('-guild_xp')[:50]
    
    return render(request, 'core/leaderboard.html', {
        'top_players': top_players,
        'top_guilds': top_guilds,
    })