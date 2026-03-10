from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from django.contrib.auth import get_user_model
from guilds.models import Guild, Quest
from core.models import EvaluationSession

User = get_user_model()

    # Super uer validation
def is_overseer(user):
    return user.is_authenticated and user.is_superuser

@user_passes_test(is_overseer, login_url='/')
def overseer_dashboard(request):
    """The main command center for platform administrators."""
    
    # Analytics
    total_users = User.objects.count()
    total_guilds = Guild.objects.count()
    total_quests = Quest.objects.filter(is_active=True).count()
    total_evals = EvaluationSession.objects.filter(status='completed').count()

    # Lists for the tables
    guilds = Guild.objects.all().select_related('founder').order_by('-created_at')
    players = User.objects.all().select_related('profile').order_by('-date_joined')

    context = {
        'total_users': total_users,
        'total_guilds': total_guilds,
        'total_quests': total_quests,
        'total_evals': total_evals,
        'guilds': guilds,
        'players': players,
    }
    return render(request, 'overseer/dashboard.html', context)


@user_passes_test(is_overseer, login_url='/')
def toggle_guild_verification(request, guild_id):
    if request.method == 'POST':
        guild = get_object_or_404(Guild, id=guild_id)
        guild.is_verified = not guild.is_verified
        guild.save()
        status = "Verified" if guild.is_verified else "Unverified"
        messages.success(request, f"Guild '{guild.name}' is now {status}.")
    return redirect('overseer_dashboard')


@user_passes_test(is_overseer, login_url='/')
def dismiss_guild(request, guild_id):
    if request.method == 'POST':
        guild = get_object_or_404(Guild, id=guild_id)
        name = guild.name
        guild.delete()
        messages.error(request, f"Guild '{name}' has been eradicated from the network.")
    return redirect('overseer_dashboard')


@user_passes_test(is_overseer, login_url='/')
def wipe_player_xp(request, user_id):
    if request.method == 'POST':
        player = get_object_or_404(User, id=user_id)
        if hasattr(player, 'profile'):
            player.profile.total_xp = 0
            player.profile.level = 1
            player.profile.save()
            messages.warning(request, f"Player '{player.username}' stats have been reset to 0.")
    return redirect('overseer_dashboard')


@user_passes_test(is_overseer, login_url='/')
def toggle_player_ban(request, user_id):
    if request.method == 'POST':
        player = get_object_or_404(User, id=user_id)
        # prevent accidential banning
        if player == request.user:
            messages.error(request, "You cannot ban yourself, Overseer.")
            return redirect('overseer_dashboard')
            
        player.is_active = not player.is_active
        player.save()
        status = "BANNED" if not player.is_active else "RESTORED"
        messages.info(request, f"Player '{player.username}' has been {status}.")
    return redirect('overseer_dashboard')