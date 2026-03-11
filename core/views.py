from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache 
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from django.core.cache import cache
from django.contrib import messages
import requests
from django.db.models import Q

from .models import UserSkill, Skill, Question, EvaluationSession, EvaluationResult
from guilds.models import Guild
from .utils import calculate_radar_stats    

# DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EvaluationSessionSerializer, QuestionSerializer
import random
from .ai_evaluator import evaluate_answer
from .tasks import process_evaluation_task

# ==========================================
# UI VIEWS
# ==========================================

def index_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/auth/register/?mode=login')

@login_required
@never_cache                          
def dashboard(request, username=None):
    # 1. Determine whose profile we are looking at (The "Hero")
    if username:
        target_user = get_object_or_404(User, username=username)
        is_owner = False
    else:
        target_user = request.user
        is_owner = True

    # 2. Handle GitHub Linking (ONLY if it's your own profile)
    if request.method == "POST" and "github_username" in request.POST and is_owner:
        github_user = request.POST.get("github_username").strip()
        request.user.profile.github_username = github_user
        request.user.profile.save()
        cache.delete(f"github_repos_{github_user}")
        messages.success(request, f"GitHub account '{github_user}' synced successfully!")
        return redirect('dashboard')

    # 3. Fetch data for TARGET_USER (The Hero)
    user_skills = UserSkill.objects.filter(user=target_user)
    radar_data = calculate_radar_stats(user_skills)
    
    profile = target_user.profile
    target_xp = profile.level * 1000 
    xp_percentage = min(int((profile.total_xp / target_xp) * 100), 100) if target_xp > 0 else 0

    user_guild = target_user.guilds.first()

    # 4. Fetch GitHub Repos
    github_repos = []
    if profile.github_username:
        cache_key = f"github_repos_{profile.github_username}"
        github_repos = cache.get(cache_key)
        if github_repos is None:
            try:
                url = f"https://api.github.com/users/{profile.github_username}/repos?sort=updated&per_page=3"
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    github_repos = response.json()
                    cache.set(cache_key, github_repos, 3600)
                else:
                    github_repos = []
            except Exception:
                github_repos = []

    # 5. Calculate Follow Stats & Status
    is_following = False
    if not is_owner:
        is_following = profile.followers.filter(id=request.user.id).exists()
        
    followers_count = profile.followers.count()
    following_count = target_user.following_profiles.count()

    context = {
        'hero': target_user,
        'is_owner': is_owner,
        'is_following': is_following,
        'followers_count': followers_count,
        'following_count': following_count,
        'skills': user_skills,
        'stats': radar_data['stats'],
        'polygon_points': radar_data['polygon_points'],
        'target_xp': target_xp,
        'xp_percentage': xp_percentage,
        'user_guild': user_guild,
        'github_repos': github_repos,
    }
    
    return render(request, 'core/dashboard.html', context)


@login_required
@never_cache
def search_view(request):
    """Handles the Global Navbar Search"""
    query = request.GET.get('q', '').strip()
    
    heroes = []
    guilds = []
    
    if query:
        # Search for players by username or first name
        heroes = User.objects.filter(
            Q(username__icontains=query) | Q(first_name__icontains=query)
        ).select_related('profile').exclude(id=request.user.id)
        
        # Search for guilds by name
        guilds = Guild.objects.filter(name__icontains=query)

    context = {
        'query': query,
        'heroes': heroes,
        'guilds': guilds,
    }
    return render(request, 'core/search_results.html', context)


@login_required
def follow_toggle(request, username):
    """Allows users to follow and unfollow each other"""
    if request.method == "POST":
        target_user = get_object_or_404(User, username=username)
        
        if target_user != request.user: # Prevent following yourself
            profile = target_user.profile
            if profile.followers.filter(id=request.user.id).exists():
                profile.followers.remove(request.user)
                messages.info(request, f"You unfollowed {username}.")
            else:
                profile.followers.add(request.user)
                messages.success(request, f"You are now following {username}!")
                
    return redirect('public_profile', username=username)


@login_required
@never_cache
def evaluation_room(request):
    """Serves the frontend interface for the AI Evaluation engine."""
    user_skills = UserSkill.objects.filter(user=request.user).select_related('skill')
    context = {'user_skills': user_skills}
    return render(request, 'core/evaluation_room.html', context)

# ==========================================
# EVALUATION API VIEWS
# ==========================================

class StartEvaluationView(APIView):
    def post(self, request):
        skill_id = request.data.get('skill_id')
        target_level = request.data.get('target_level', 1)
        
        skill = get_object_or_404(Skill, id=skill_id)
        questions = Question.objects.filter(skill=skill, target_level=target_level)
        if not questions.exists():
            return Response({"error": "No questions found for this skill/level."}, status=status.HTTP_404_NOT_FOUND)
            
        selected_question = random.choice(questions)
        deadline = timezone.now() + timedelta(seconds=selected_question.time_limit_seconds)
        
        session = EvaluationSession.objects.create(
            user=request.user, 
            skill=skill, 
            target_level=target_level,
            status='in_progress',
            expected_end=deadline
        )
        
        return Response({
            "session_id": session.id,
            "question": QuestionSerializer(selected_question).data
        }, status=status.HTTP_201_CREATED)
        

class SubmitAnswerView(APIView):
    def post(self, request, session_id):
        session = get_object_or_404(EvaluationSession, id=session_id, user=request.user)
        user_answer = request.data.get('answer_text')
        question_id = request.data.get('question_id') 
        
        if session.expected_end and timezone.now() > session.expected_end:
            session.status = 'abandoned'
            session.save()
            return Response({"error": "Time limit exceeded."}, status=status.HTTP_403_FORBIDDEN)
            
        if session.status != 'in_progress':
            return Response({"error": "Session is not active."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_answer or not question_id:
            return Response({"error": "answer_text and question_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        session.status = 'evaluating'
        session.save()
        
        process_evaluation_task.delay(session.id, question_id, user_answer)
        
        return Response({
            "message": "Answer received. AI evaluation in progress.",
            "status": session.status
        }, status=status.HTTP_202_ACCEPTED)
        
class CheckEvaluationStatusView(APIView):
    def get(self, request, session_id):
        session = get_object_or_404(EvaluationSession, id=session_id, user=request.user)
        
        if session.status == 'evaluating':
            return Response({"status": "evaluating", "message": "AI is still thinking..."})
            
        if session.status == 'completed':
            result = get_object_or_404(EvaluationResult, session=session)
            
            # --- CALCULATED EXACT XP CHANGE ---
            if result.level_awarded >= session.target_level:
                xp_change = f"+{session.target_level * 100} XP"
            else:
                xp_change = f"-{session.target_level * 50} XP"
            
            return Response({
                "status": "completed",
                "level_awarded": result.level_awarded,
                "reasoning": result.reasoning,
                "strengths": result.strengths,
                "gaps": result.gaps,
                "new_total_xp": xp_change 
            }, status=status.HTTP_200_OK)
            
        return Response({"status": session.status})