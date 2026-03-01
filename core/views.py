from django.shortcuts import render,redirect, get_object_or_404
from django.contrib.auth.decorators import login_required 
from django.views.decorators.cache import never_cache 
from .models import UserSkill,Skill, Question, EvaluationSession
from .utils import calculate_radar_stats    


#DRF imports
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EvaluationSessionSerializer, QuestionSerializer
import random
from .ai_evaluator import evaluate_answer


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
    return render(request, 'core/dashboard.html',context)


# NEW EVALUATION API VIEWS

class StartEvaluationView(APIView):
    """Creates a new session and returns a random question for the chosen skill/level."""
    
    def post(self, request):
        skill_id = request.data.get('skill_id')
        target_level = request.data.get('target_level', 1)
        
        # 1. Validate the skill exists
        skill = get_object_or_404(Skill, id=skill_id)
        
        # 2. Create the Session
        session = EvaluationSession.objects.create(
            user=request.user, 
            skill=skill, 
            target_level=target_level,
            status='in_progress'
        )
        
        # 3. Fetch a matching question
        questions = Question.objects.filter(skill=skill, target_level=target_level)
        if not questions.exists():
            return Response({"error": "No questions found for this skill/level."}, status=status.HTTP_404_NOT_FOUND)
            
        selected_question = random.choice(questions)
        
        # 4. Return the session ID and the question to the user
        return Response({
            "session_id": session.id,
            "question": QuestionSerializer(selected_question).data
        }, status=status.HTTP_201_CREATED)


class SubmitAnswerView(APIView):
    """Receives the user's text answer, triggers AI evaluation, and returns the grade."""
    
    def post(self, request, session_id):
        session = get_object_or_404(EvaluationSession, id=session_id, user=request.user)
        user_answer = request.data.get('answer_text')
        question_id = request.data.get('question_id') # We must know which question they answered
        
        if session.status != 'in_progress':
            return Response({"error": "This session is no longer active."}, status=status.HTTP_400_BAD_REQUEST)
            
        if not user_answer or not question_id:
            return Response({"error": "answer_text and question_id are required."}, status=status.HTTP_400_BAD_REQUEST)

        question = get_object_or_404(Question, id=question_id)

        # 1. Update session status
        session.status = 'evaluating'
        session.save()
        
        # 2. Trigger the AI Engine (Synchronous for the MVP)
        result = evaluate_answer(session, question, user_answer)
        
        if not result:
            session.status = 'in_progress' # Rollback if AI fails
            session.save()
            return Response({"error": "AI Evaluation failed. Please try again."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # 3. Return the final grade!
        return Response({
            "message": "Evaluation Complete",
            "level_awarded": result.level_awarded,
            "reasoning": result.reasoning,
            "strengths": result.strengths,
            "gaps": result.gaps
        }, status=status.HTTP_200_OK)