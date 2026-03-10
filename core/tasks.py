from celery import shared_task
from .models import EvaluationSession, Question, UserSkill
from .ml_router import evaluate_with_hybrid_routing
from users.models import Profile  # We need the global profile now!

@shared_task
def process_evaluation_task(session_id, question_id, user_answer):
    """
    Background worker task to call the AI, enforce pass/fail logic, and update XP.
    """
    try:
        session = EvaluationSession.objects.get(id=session_id)
        question = Question.objects.get(id=question_id)
    except (EvaluationSession.DoesNotExist, Question.DoesNotExist):
        return "Task Failed: Session or Question not found."

    # 1. Trigger the AI Engine
    result = evaluate_with_hybrid_routing(session, question, user_answer)
    
    if not result:
        session.status = 'in_progress' 
        session.save()
        return "Task Failed: Evaluation routing returned None."
    
    # 2. Fetch the UserSkill and Global Profile
    user_skill, _ = UserSkill.objects.get_or_create(
        user=session.user,
        skill=session.skill
    )
    profile = Profile.objects.get(user=session.user)

    # 3. PASS/FAIL LOGIC & XP MATH
    xp_change = 0
    target = session.target_level
    awarded = result.level_awarded

    if awarded >= target:
        # --- SUCCESS PROTOCOL ---
        # Only level them up if the target level is higher than their current
        if target > user_skill.level:
            user_skill.level = target
            
        xp_change = target * 100  # Example: Pass Lvl 3 = +300 XP
        
        # Add a success note to the reasoning for the frontend
        result.reasoning = f"[CHALLENGE PASSED] {result.reasoning}"
        result.save()
        
    else:
        # --- FAIL PROTOCOL ---
        xp_change = -(target * 50) # Example: Fail Lvl 3 = -150 XP
        
        # We rewrite the awarded level in the DB to 0 so the frontend knows they failed
        result.level_awarded = 0
        result.reasoning = f"[CHALLENGE FAILED - Insufficient knowledge for Level {target}] {result.reasoning}"
        result.save()

    # 4. Apply the Math (Capped at 0)
    user_skill.xp = max(0, user_skill.xp + xp_change)
    profile.total_xp = max(0, profile.total_xp + xp_change)

    while profile.total_xp >= (profile.level * 1000):
        
            profile.total_xp -= (profile.level * 1000)
            profile.level += 1
            
    # 5. Handle Level Downgrades (If XP drops too low)
    # The required XP for their CURRENT level is (level * 1000)
    # If they drop below the requirement for the PREVIOUS level, they de-level.
    # We never drop them below Level 1.
    if user_skill.level > 1:
        xp_needed_for_current_level = (user_skill.level - 1) * 1000
        if user_skill.xp < xp_needed_for_current_level:
            user_skill.level -= 1

    # Save everything
    user_skill.save()
    profile.save()
    
    status_msg = "PASSED" if awarded >= target else "FAILED"
    return f"Task Complete: Challenge {status_msg}. XP Change: {xp_change}"