from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from .models import Guild, Quest

@login_required
def guild_dashboard(request):
    user = request.user
    user_guilds = user.guilds.all()
    
    if user_guilds.exists():
        my_guild = user_guilds.first() 
        active_quests = my_guild.quests.filter(is_active=True).order_by('-created_at')
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

@login_required
def join_guild(request, guild_id):
    if request.method == 'POST':
        guild = get_object_or_404(Guild, id=guild_id)
        user_level = request.user.profile.level if hasattr(request.user, 'profile') else 1
        
        # Check if the user meets the level requirement
        if user_level >= guild.minimum_level_to_join:
            guild.members.add(request.user)
            messages.success(request, f"Welcome to {guild.name}, Mercenary!")
        else:
            messages.error(request, f"Access Denied: You must be Level {guild.minimum_level_to_join} to join this guild.")
            
    return redirect('guild_dashboard')

@login_required
def leave_guild(request):
    if request.method == 'POST':
        user_guilds = request.user.guilds.all()
        if user_guilds.exists():
            guild = user_guilds.first()
            guild.members.remove(request.user)
            messages.info(request, f"You have abandoned {guild.name}.")
    return redirect('guild_dashboard')

@login_required
def create_guild(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        industry = request.POST.get('industry')
        description = request.POST.get('description')
        min_level = request.POST.get('min_level', 1)

        # Prevent duplicate guild names
        if Guild.objects.filter(name__iexact=name).exists():
            messages.error(request, "A guild with this exact name already exists in the registry.")
            return redirect('create_guild')

        # Create the Guild
        guild = Guild.objects.create(
            name=name,
            slug=slugify(name),
            industry=industry,
            description=description,
            minimum_level_to_join=int(min_level),
            founder=request.user
        )
        # Add the founder as the first member
        guild.members.add(request.user)
        messages.success(request, f"Guild {guild.name} founded successfully! You are now the Archon.")
        return redirect('guild_dashboard')

    return render(request, 'guilds/create_guild.html')