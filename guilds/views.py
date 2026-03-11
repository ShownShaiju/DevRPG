from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils.text import slugify
from .models import Guild, Quest
from core.models import UserSkill
from django.contrib import messages
from users.models import Profile
from .models import Quest, QuestSubmission

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

@login_required
def quest_board(request):
    """The global job board where players browse available bounties."""
    
    # 1. Map the user's current skills into a fast dictionary {skill_id: level}
    user_skills_dict = {
        us.skill.id: us.level 
        for us in UserSkill.objects.filter(user=request.user).select_related('skill')
    }

    # 2. Fetch all active quests and their requirements
    quests = Quest.objects.filter(is_active=True).select_related('guild').prefetch_related('requirements__skill').order_by('-created_at')
    
    # 3. Calculate Eligibility
    for quest in quests:
        quest.is_eligible = True
        quest.missing_skills = [] 
        
        for req in quest.requirements.all():
            user_level = user_skills_dict.get(req.skill.id, 0)
            
            req.user_level = user_level
            req.is_met = user_level >= req.minimum_level
            
            if not req.is_met:
                quest.is_eligible = False
                quest.missing_skills.append(f"Lv.{req.minimum_level} {req.skill.name}")

    context = {
        'quests': quests,
    }
    return render(request, 'guilds/quest_board.html', context)

@login_required
def create_quest(request):
    """Allows Guild Owners to post new bounties."""
    if request.method == "POST":
        guild = request.user.guilds.first()
        if not guild or guild.founder != request.user:
            messages.error(request, "Only Guild Founders can issue quests.")
            return redirect('guild_dashboard')
            
        title = request.POST.get('title')
        description = request.POST.get('description')
        xp_reward = int(request.POST.get('xp_reward', 500))
        
        Quest.objects.create(guild=guild, title=title, description=description, xp_reward=xp_reward)
        messages.success(request, f"Quest '{title}' has been posted to the bounty board!")
        
    return redirect('guild_dashboard')

@login_required
def accept_quest(request, quest_id):
    """Player accepts a quest to work on it."""
    quest = get_object_or_404(Quest, id=quest_id)
    
    # Check if they already took it
    if QuestSubmission.objects.filter(quest=quest, user=request.user).exists():
        messages.error(request, "You have already accepted this quest.")
    else:
        QuestSubmission.objects.create(quest=quest, user=request.user)
        messages.success(request, "Quest Accepted! Good luck, hero.")
        
    return redirect('quest_board')

@login_required
def submit_quest(request, quest_id):
    """Player submits their GitHub link for review."""
    if request.method == "POST":
        quest = get_object_or_404(Quest, id=quest_id)
        submission = get_object_or_404(QuestSubmission, quest=quest, user=request.user)
        
        github_url = request.POST.get('github_url')
        if github_url:
            submission.github_url = github_url
            submission.status = 'submitted'
            submission.save()
            messages.success(request, "Results submitted to the Guild Overseer for review.")
            
    return redirect('quest_board')

@login_required
def approve_submission(request, submission_id):
    """Guild Owner approves the code, grants XP, and closes the quest."""
    submission = get_object_or_404(QuestSubmission, id=submission_id)
    quest = submission.quest
    
    # Security: Only the Guild Founder who issued the quest can approve it
    if quest.guild.founder == request.user:
        # 1. Update submission
        submission.status = 'approved'
        submission.save()
        
        # 2. Grant XP to the player who submitted it
        profile = submission.user.profile
        profile.total_xp += quest.xp_reward
        
        # Handle Level Ups!
        while profile.total_xp >= (profile.level * 1000):
            profile.total_xp -= (profile.level * 1000)
            profile.level += 1
        profile.save()
        
        # 3. Close the quest so no one else can submit
        quest.is_active = False
        quest.save()
        
        messages.success(request, f"Bounty Paid! {submission.user.username} was awarded {quest.xp_reward} XP.")
    else:
        messages.error(request, "You do not have authorization to approve this quest.")
        
    return redirect('guild_dashboard')