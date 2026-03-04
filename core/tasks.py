from celery import shared_task
from .models import EvaluationSession, Question, UserSkill
from .ml_router import evaluate_with_hybrid_routing # Add this import

@shared_task
def process_evaluation_task(session_id, question_id, user_answer):
    """
    Background worker task to call the AI and update user progress.
    """
    try:
        session = EvaluationSession.objects.get(id=session_id)
        question = Question.objects.get(id=question_id)
    except (EvaluationSession.DoesNotExist, Question.DoesNotExist):
        return "Task Failed: Session or Question not found."

    # 1. Trigger the Hybrid Routing Engine (DistilBERT -> Gemini)
    result = evaluate_with_hybrid_routing(session, question, user_answer)
    
    if not result:
        session.status = 'in_progress' 
        session.save()
        return "Task Failed: Evaluation routing returned None."
    
    # 2. Update User Level and XP
    user_skill, _ = UserSkill.objects.get_or_create(
        user=session.user,
        skill=session.skill
    )

    if result.level_awarded > user_skill.level:
        user_skill.level = result.level_awarded
        
    user_skill.xp += (result.level_awarded * 100)
    user_skill.save()
    
    return f"Task Complete: Awarded Level {result.level_awarded}"