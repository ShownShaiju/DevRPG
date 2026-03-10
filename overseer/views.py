from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import get_user_model
from guilds.models import Guild, Quest
from core.models import EvaluationSession
import time
from datetime import timedelta
from django.apps import apps

User = get_user_model()
SERVER_BOOT_TIME = time.time()

# --- THE CUSTOM SECURITY GATEWAY ---
def overseer_clearance_required(view_func):
    """Strictly blocks non-admins and handles redirects cleanly."""
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Authentication required to access the Overseer Nexus.")
            return redirect('login') # Sends them to your custom DevRPG login page
            
        if not request.user.is_superuser:
            messages.error(request, "ACCESS DENIED: Insufficient clearance level.")
            return redirect('dashboard') # Kicks regular players back to their profile
            
        return view_func(request, *args, **kwargs)
    return wrapper

@overseer_clearance_required
def overseer_dashboard(request):
    total_users = User.objects.count()
    total_guilds = Guild.objects.count()
    total_quests = Quest.objects.filter(is_active=True).count()
    total_evals = EvaluationSession.objects.filter(status='completed').count()

    guilds = Guild.objects.all().select_related('founder').order_by('-created_at')
    players = User.objects.all().select_related('profile').order_by('-date_joined')

    # Calculate the exact seconds since the file was loaded into memory
    uptime_seconds = int(time.time() - SERVER_BOOT_TIME)

    context = {
        'total_users': total_users,
        'total_guilds': total_guilds,
        'total_quests': total_quests,
        'total_evals': total_evals,
        'guilds': guilds,
        'players': players,
        'uptime_seconds': uptime_seconds,
    }
    return render(request, 'overseer/dashboard.html', context)

@overseer_clearance_required
def toggle_guild_verification(request, guild_id):
    if request.method == 'POST':
        guild = get_object_or_404(Guild, id=guild_id)
        guild.is_verified = not guild.is_verified
        guild.save()
        status = "Verified" if guild.is_verified else "Unverified"
        messages.success(request, f"Guild '{guild.name}' is now {status}.")
    return redirect('overseer_dashboard')

@overseer_clearance_required
def dismiss_guild(request, guild_id):
    if request.method == 'POST':
        guild = get_object_or_404(Guild, id=guild_id)
        name = guild.name
        guild.delete()
        messages.error(request, f"Guild '{name}' has been eradicated from the network.")
    return redirect('overseer_dashboard')

@overseer_clearance_required
def wipe_player_xp(request, user_id):
    if request.method == 'POST':
        player = get_object_or_404(User, id=user_id)
        if hasattr(player, 'profile'):
            player.profile.total_xp = 0
            player.profile.level = 1
            player.profile.save()
            messages.warning(request, f"Player '{player.username}' stats have been reset to 0.")
    return redirect('overseer_dashboard')

@overseer_clearance_required
def toggle_player_ban(request, user_id):
    if request.method == 'POST':
        player = get_object_or_404(User, id=user_id)
        if player == request.user:
            messages.error(request, "You cannot ban yourself, Overseer.")
            return redirect('overseer_dashboard')
            
        player.is_active = not player.is_active
        player.save()
        status = "BANNED" if not player.is_active else "RESTORED"
        messages.info(request, f"Player '{player.username}' has been {status}.")
    return redirect('overseer_dashboard')