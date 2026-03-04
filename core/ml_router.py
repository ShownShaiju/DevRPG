import os
import logging
from transformers import pipeline
from django.conf import settings
from .ai_evaluator import evaluate_answer
from .models import EvaluationResult

logger = logging.getLogger(__name__)

# --- IN-MEMORY MODEL INITIALIZATION ---
# This executes once when the Celery worker boots.
MODEL_PATH = os.path.join(settings.BASE_DIR, 'core', 'ml_models', 'distilbert_skill_classifier')

try:
    # top_k=None ensures we get probabilities for all classes
    classifier = pipeline("text-classification", model=MODEL_PATH, top_k=None)
    LOCAL_MODEL_AVAILABLE = True
    print(f"[\u2713] Custom DistilBERT loaded into worker RAM from {MODEL_PATH}")
except Exception as e:
    print(f"[!] Local model offline. Defaulting 100% of traffic to Gemini. Error: {e}")
    LOCAL_MODEL_AVAILABLE = False


def evaluate_with_hybrid_routing(session, question, user_answer):
    """
    Two-Tier Cascade Architecture:
    1. Fast Path: Local DistilBERT inference (Milliseconds).
    2. Fallback Path: Gemini API if confidence is below the threshold.
    """
    
    if LOCAL_MODEL_AVAILABLE:
        try:
            # 1. Run Local Inference
            predictions = classifier(user_answer)[0]
            
            # 2. Extract highest probability
            best_pred = max(predictions, key=lambda x: x['score'])
            confidence = best_pred['score']
            
            # 3. The Analytics Gatekeeper (Threshold: 85%)
            if confidence >= 0.85:
                
                # Map standard HuggingFace labels (e.g., LABEL_0) to your 1-5 levels
                label_str = best_pred['label']
                level = int(''.join(filter(str.isdigit, label_str)))
                if "LABEL" in label_str.upper(): 
                    level += 1 # Adjusting for 0-indexed training arrays
                
                # Constrain to 1-5 bounds
                level = max(1, min(level, 5))

                # 4. Fast Path DB Execution (Bypass API entirely)
                result = EvaluationResult.objects.create(
                    session=session,
                    level_awarded=level,
                    confidence=confidence,
                    # We synthesize the detailed feedback since DistilBERT only outputs classes
                    reasoning=f"[\u26A1 Fast-Path Evaluation] Analyzed locally in milliseconds via DevRPG DistilBERT. The model is {confidence*100:.1f}% confident this answer aligns with a Level {level} understanding.",
                    strengths=["Recognized standard vocabulary and structural patterns for this tier."],
                    gaps=["(Deep rubric analysis skipped due to high confidence baseline match)"],
                    rubric_scores={},
                    ai_raw_response={"router": "local_distilbert", "predictions": predictions},
                    ai_assisted_flag=False 
                )
                
                session.status = 'completed'
                session.save()
                return result
                
        except Exception as e:
            logger.error(f"DistilBERT inference pipeline failed: {e}. Executing Fallback.")

    # 5. Slow Path Execution (Gemini API)
    # Triggered if DistilBERT is uncertain (< 85%) or offline
    return evaluate_answer(session, question, user_answer)