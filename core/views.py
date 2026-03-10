from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache 
from django.utils import timezone
from datetime import timedelta

from .models import UserSkill, Skill, Question, EvaluationSession
from .utils import calculate_radar_stats    

# DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EvaluationSessionSerializer, QuestionSerializer
import random
from .ai_evaluator import evaluate_answer
from .tasks import process_evaluation_task
from .models import EvaluationResult
from django.contrib import messages
import requests
from django.core.cache import cache
# ==========================================
# UI VIEWS
# ==========================================

def index_redirect(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return redirect('/auth/register/?mode=login')

@login_required
@never_cache                          
def dashboard(request):
    
    if request.method == "POST" and "github_username" in request.POST:
        github_user = request.POST.get("github_username").strip()
        request.user.profile.github_username = github_user
        request.user.profile.save()
        
        # Clear any old cached data just in case they are changing usernames
        cache_key = f"github_repos_{github_user}"
        cache.delete(cache_key)
        
        messages.success(request, f"GitHub account '{github_user}' synced successfully!")
        return redirect('dashboard')
    
    user_skills = UserSkill.objects.filter(user=request.user)
    radar_data = calculate_radar_stats(user_skills)
    
    profile = request.user.profile
    target_xp = profile.level * 1000 
    

    if target_xp > 0:
        xp_percentage = min(int((profile.total_xp / target_xp) * 100), 100)
    else:
        xp_percentage = 0
    
    user_guild = request.user.guilds.first()
    github_repos = []
    if profile.github_username:
        # Cache the API response for 1 hour (3600 seconds) so we don't hit rate limits
        cache_key = f"github_repos_{profile.github_username}"
        github_repos = cache.get(cache_key)

        if github_repos is None:
            try:
                # Fetch the 3 most recently updated public repos
                url = f"https://api.github.com/users/{profile.github_username}/repos?sort=updated&per_page=3"
                response = requests.get(url, timeout=3)
                if response.status_code == 200:
                    github_repos = response.json()
                    cache.set(cache_key, github_repos, 3600) # Save to cache
                else:
                    github_repos = []
            except Exception as e:
                print(f"GitHub API Error: {e}")
                github_repos = []
    # -----------------------------------

    context = {
        'skills': user_skills,
        'stats': radar_data['stats'],
        'polygon_points': radar_data['polygon_points'],
        'target_xp': target_xp,
        'xp_percentage': xp_percentage,
        'user_guild': user_guild,
        'github_repos': github_repos, # Pass the repos to the template!
    }
    
    return render(request, 'core/dashboard.html', context)
@login_required
@never_cache
def evaluation_room(request):
    """Serves the frontend interface for the AI Evaluation engine."""
    # Fetch the user's active skills so they can select what to test
    user_skills = UserSkill.objects.filter(user=request.user).select_related('skill')
    
    context = {
        'user_skills': user_skills
    }
    return render(request, 'core/evaluation_room.html', context)

# EVALUATION API VIEWS

class StartEvaluationView(APIView):
    """Creates a new session, sets a deadline, and returns a random question."""
    
    def post(self, request):
        skill_id = request.data.get('skill_id')
        target_level = request.data.get('target_level', 1)
        
        # 1. Validate the skill exists
        skill = get_object_or_404(Skill, id=skill_id)
        
        # 2. Fetch a matching question FIRST to get the time limit
        questions = Question.objects.filter(skill=skill, target_level=target_level)
        if not questions.exists():
            return Response({"error": "No questions found for this skill/level."}, status=status.HTTP_404_NOT_FOUND)
            
        selected_question = random.choice(questions)
        
        # 3. Calculate deadline and create Session
        deadline = timezone.now() + timedelta(seconds=selected_question.time_limit_seconds)
        
        session = EvaluationSession.objects.create(
            user=request.user, 
            skill=skill, 
            target_level=target_level,
            status='in_progress',
            expected_end=deadline
        )
        
        # 4. Return the session ID and the question to the user
        return Response({
            "session_id": session.id,
            "question": QuestionSerializer(selected_question).data
        }, status=status.HTTP_201_CREATED)
        

class SubmitAnswerView(APIView):
    """Receives the answer, enforces the timer, and dispatches a background task."""
    
    def post(self, request, session_id):
        session = get_object_or_404(EvaluationSession, id=session_id, user=request.user)
        user_answer = request.data.get('answer_text')
        question_id = request.data.get('question_id') 
        
        # 1. Timer Enforcement
        if session.expected_end and timezone.now() > session.expected_end:
            session.status = 'abandoned'
            session.save()
            return Response({"error": "Time limit exceeded."}, status=status.HTTP_403_FORBIDDEN)
            
        # 2. Validation
        if session.status != 'in_progress':
            return Response({"error": "Session is not active."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_answer or not question_id:
            return Response({"error": "answer_text and question_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        # 3. Update session status to indicate background processing
        session.status = 'evaluating'
        session.save()
        
        # 4. Dispatch the Celery Task (.delay() makes it asynchronous)
        process_evaluation_task.delay(session.id, question_id, user_answer)
        
        # 5. Instantly return a 202 Accepted (Processing)
        return Response({
            "message": "Answer received. AI evaluation in progress.",
            "status": session.status
        }, status=status.HTTP_202_ACCEPTED)
        
class CheckEvaluationStatusView(APIView):
    """Allows the client to check if the AI has finished grading."""
    
    def get(self, request, session_id):
        session = get_object_or_404(EvaluationSession, id=session_id, user=request.user)
        
        if session.status == 'evaluating':
            return Response({"status": "evaluating", "message": "AI is still thinking..."})
            
        if session.status == 'completed':
            result = get_object_or_404(EvaluationResult, session=session)
            
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