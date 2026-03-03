from rest_framework import serializers
from .models import Skill, Question, EvaluationSession, EvaluationResult

class SkillSerializer(serializers.ModelSerializer):
    class Meta:
        model = Skill
        fields = ['id', 'name', 'category', 'rarity', 'icon']

class QuestionSerializer(serializers.ModelSerializer):

    class Meta:
        model = Question
        fields = ['id', 'target_level', 'scenario', 'task']

class EvaluationSessionSerializer(serializers.ModelSerializer):
    skill = SkillSerializer(read_only=True)
    
    class Meta:
        model = EvaluationSession
        fields = ['id', 'user', 'skill', 'target_level', 'status', 'started_at']