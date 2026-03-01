import json
import google.generativeai as genai
from django.conf import settings
from .models import EvaluationResult

# Ensure your key is set in settings.py
genai.configure(api_key=settings.GEMINI_API_KEY)

def evaluate_answer(session, question, user_answer):
    """Sends the answer and rubric to the AI and saves the result to the database."""
    
    rubric_items = question.rubric_items.all()
    rubric_text = "\n".join([f"- ID {r.id}: {r.description} (Weight: {r.weight})" for r in rubric_items])
    
    prompt = f"""
    You are an elite senior developer evaluating a candidate's technical answer.
    
    Skill: {question.skill.name}
    Target Level (1-5): {question.target_level}
    
    Scenario given to candidate:
    {question.scenario}
    
    Candidate's Answer:
    {user_answer}
    
    Evaluate the answer based strictly on these rubric items:
    {rubric_text}
    
    Return ONLY a raw JSON object with the following structure:
    {{
        "level_awarded": int (1 to 5),
        "confidence": float (0.0 to 1.0),
        "reasoning": "2-3 sentences explaining the score",
        "strengths": ["strength 1", "strength 2"],
        "gaps": ["gap 1", "gap 2"],
        "rubric_scores": {{"rubric_id_1": true, "rubric_id_2": false}}
    }}
    """
    
    try:
        # Using the model you suggested
        model = genai.GenerativeModel('gemini-2.5-flash')
        response = model.generate_content(prompt)
        
        # Robust JSON cleaning
        raw_text = response.text.strip()
        if raw_text.startswith("```json"):
            raw_text = raw_text.replace("```json", "", 1).replace("```", "", 1).strip()
        elif raw_text.startswith("```"):
            raw_text = raw_text.replace("```", "", 2).strip()
            
        ai_data = json.loads(raw_text)
        
        # Save the result
        result = EvaluationResult.objects.create(
            session=session,
            level_awarded=ai_data.get('level_awarded', 1),
            confidence=ai_data.get('confidence', 0.5),
            reasoning=ai_data.get('reasoning', "Evaluation complete."),
            strengths=ai_data.get('strengths', []),
            gaps=ai_data.get('gaps', []),
            rubric_scores=ai_data.get('rubric_scores', {}),
            ai_raw_response=ai_data
        )
        
        session.status = 'completed'
        session.save()
        
        return result
        
    except Exception as e:
        # This will now print the specific error to your terminal
        print(f"AI Evaluation Failed: {e}")
        return None