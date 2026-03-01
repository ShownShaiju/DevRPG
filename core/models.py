from django.db import models
from django.contrib.auth.models import User

# --- YOUR EXISTING MODELS ---
class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.title

# --- EVALUATION ENGINE MODELS ---
class Skill(models.Model):
    RARITY_CHOICES = [
        ('common', 'Common'),
        ('rare', 'Rare'),
        ('epic', 'Epic'),
        ('legendary', 'Legendary'),
    ]
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, null=True, blank=True)
    rarity = models.CharField(max_length=20, choices=RARITY_CHOICES, default='common')
    category = models.CharField(max_length=100)
    description = models.TextField(blank=True, default="")
    icon = models.CharField(max_length=50, blank=True, default="")
    is_active = models.BooleanField(default=True)
    
    merge_sources = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='merge_results')
    merge_min_level = models.PositiveSmallIntegerField(default=3)

    def __str__(self):
        return f"{self.name} ({self.rarity})"

class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='skill_profiles')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    level = models.IntegerField(default=1) # Renamed from current_level to match your original
    xp = models.IntegerField(default=0)
    
    class Meta:
        unique_together = ('user', 'skill')

    def __str__(self):
        return f"{self.user.username} - {self.skill.name} (Lvl {self.level})"

class Question(models.Model):
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE, related_name='questions')
    target_level = models.PositiveSmallIntegerField()
    scenario = models.TextField()
    task = models.TextField()
    time_limit_seconds = models.PositiveIntegerField(default=480)
    difficulty_notes = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.skill.name} Lvl {self.target_level} Question"

class RubricItem(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='rubric_items')
    description = models.TextField()
    weight = models.FloatField(default=1.0)
    level_gate = models.PositiveSmallIntegerField()
    order = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.description

class EvaluationSession(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('evaluating', 'Evaluating'),
        ('completed', 'Completed'),
        ('abandoned', 'Abandoned'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sessions')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    target_level = models.PositiveSmallIntegerField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    started_at = models.DateTimeField(auto_now_add=True)
    expected_end = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Session: {self.user.username} - {self.skill.name}"

class EvaluationResult(models.Model):
    session = models.OneToOneField(EvaluationSession, on_delete=models.CASCADE, related_name='result')
    level_awarded = models.PositiveSmallIntegerField()
    confidence = models.FloatField()
    reasoning = models.TextField()
    strengths = models.JSONField(default=list)
    gaps = models.JSONField(default=list)
    rubric_scores = models.JSONField(default=dict)
    ai_raw_response = models.JSONField(default=dict)
    ai_assisted_flag = models.BooleanField(default=False)
    evaluated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Result: Level {self.level_awarded}"