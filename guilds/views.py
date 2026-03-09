from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Guild, Quest

@login_required
def guild_dashboard(request):
    user = request.user
    
    # Check if the user is currently in a guild
    user_guilds = user.guilds.all()
    
    if user_guilds.exists():
        # STATE 2: The user is in a Guild
        my_guild = user_guilds.first() # For now, assume a player can only be in one guild at a time
        active_quests = my_guild.quests.filter(is_active=True).order_settings('-created_at')
        roster = my_guild.members.all().select_related('profile')
        
        context = {
            'in_guild': True,
            'guild': my_guild,
            'quests': active_quests,
            'roster': roster,
            'founder': my_guild.founder,
        }
        return render(request, 'guilds/dashboard.html', context)
        
    else:

        all_guilds = Guild.objects.all().prefetch_related('members')
        
        context = {
            'in_guild': False,
            'available_guilds': all_guilds,
        }
        return render(request, 'guilds/dashboard.html', context)