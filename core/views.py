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
    user_skills = UserSkill.objects.filter(user=request.user)
    radar_data = calculate_radar_stats(user_skills)
    
    context = {
        'skills': user_skills,
        'stats': radar_data['stats'],
        'polygon_points': radar_data['polygon_points'],
    }
    return render(request, 'core/dashboard.html', context)


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
    """Receives the answer, enforces the timer, triggers AI, and updates XP."""
    
    def post(self, request, session_id):
        session = get_object_or_404(EvaluationSession, id=session_id, user=request.user)
        user_answer = request.data.get('answer_text')
        question_id = request.data.get('question_id') 
        
        # 1. Timer Enforcement
        if session.expected_end and timezone.now() > session.expected_end:
            session.status = 'abandoned'
            session.save()
            return Response({
                "error": "Time limit exceeded. This challenge has been closed."
            }, status=status.HTTP_403_FORBIDDEN)
            
        # 2. Validation
        if session.status != 'in_progress':
            return Response({"error": "This session is no longer active."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_answer or not question_id:
            return Response({"error": "answer_text and question_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        question = get_object_or_404(Question, id=question_id)

        # 3. Update session status
        session.status = 'evaluating'
        session.save()
        
        # 4. Trigger the AI Engine
        result = evaluate_answer(session, question, user_answer)
        
        if not result:
            session.status = 'in_progress' # Rollback if AI fails
            session.save()
            return Response({"error": "AI Evaluation failed. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 5. Core Game Loop: Update User Level and XP
        user_skill, created = UserSkill.objects.get_or_create(
            user=request.user,
            skill=session.skill
        )

        if result.level_awarded > user_skill.level:
            user_skill.level = result.level_awarded
            
        user_skill.xp += (result.level_awarded * 100)
        user_skill.save()
        
        # 6. Return the final grade
        return Response({
            "message": "Evaluation Complete",
            "level_awarded": result.level_awarded,
            "reasoning": result.reasoning,
            "strengths": result.strengths,
            "gaps": result.gaps,
            "new_total_xp": user_skill.xp
        }, status=status.HTTP_200_OK)