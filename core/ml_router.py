import os
import logging
import threading
from transformers import pipeline
from django.conf import settings
from .ai_evaluator import evaluate_answer
from .models import EvaluationResult

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(settings.BASE_DIR, 'core', 'ml_models', 'distilbert_skill_classifier')

_classifier = None
_model_load_attempted = False
_model_lock = threading.Lock()  # Prevents double-load if two tasks arrive simultaneously
LOCAL_MODEL_AVAILABLE = False


def get_classifier():
    """
    Lazy Loader with thread safety.
    Model only enters RAM on the first actual evaluation request,
    not on Django server boot or auto-reload.
    """
    global _classifier, _model_load_attempted, LOCAL_MODEL_AVAILABLE

    if _model_load_attempted:
        return _classifier

    with _model_lock:
        # Double-checked locking: re-check after acquiring the lock
        # because another thread may have loaded it while we were waiting
        if not _model_load_attempted:
            _model_load_attempted = True
            try:
                _classifier = pipeline(
                    "text-classification",
                    model=MODEL_PATH,
                    top_k=None,
                    device=-1  # Force CPU — avoids CUDA auto-detect issues in containers
                )
                LOCAL_MODEL_AVAILABLE = True
                print(f"[✓] DistilBERT loaded into CPU RAM from {MODEL_PATH}")
            except Exception as e:
                print(f"[!] Local model offline. Routing 100% to Gemini. Error: {e}")
                LOCAL_MODEL_AVAILABLE = False

    return _classifier


def evaluate_with_hybrid_routing(session, question, user_answer):
    """
    Two-Tier Cascade Architecture:
    1. Fast Path: Local DistilBERT inference (Milliseconds).
    2. Fallback Path: Gemini API if confidence is below threshold or model is offline.
    """
    classifier = get_classifier()

    if LOCAL_MODEL_AVAILABLE and classifier:
        try:
            predictions = classifier(user_answer)[0]

            best_pred = max(predictions, key=lambda x: x['score'])
            confidence = best_pred['score']

            if confidence >= 0.85:
                label_str = best_pred['label']
                level = int(''.join(filter(str.isdigit, label_str)))
                if "LABEL" in label_str.upper():
                    level += 1  # Adjusting for 0-indexed training labels

                level = max(1, min(level, 5))

                result = EvaluationResult.objects.create(
                    session=session,
                    level_awarded=level,
                    confidence=confidence,
                    reasoning=f"[⚡ Fast-Path Evaluation] Analyzed locally via DevRPG DistilBERT. {confidence*100:.1f}% confident → Level {level}.",
                    strengths=["Recognized standard vocabulary and structural patterns for this tier."],
                    gaps=["(Deep rubric analysis skipped — high confidence baseline match)"],
                    rubric_scores={},
                    ai_raw_response={"router": "local_distilbert", "predictions": predictions},
                    ai_assisted_flag=False
                )

                session.status = 'completed'
                session.save()
                return result

        except Exception as e:
            logger.error(f"DistilBERT inference failed: {e}. Falling back to Gemini.")

    return evaluate_answer(session, question, user_answer)