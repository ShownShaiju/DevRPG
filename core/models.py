from django.db import models
from django.contrib.auth.models import User

# 1. STANDALONE SKILLS DATABASE (The "Dropdown" List)
class Skill(models.Model):
    CATEGORY_CHOICES = [
        ('frontend', 'Frontend'),
        ('backend', 'Backend'),
        ('cloud', 'Cloud'),
        ('mobile', 'Mobile'),
        ('tools', 'Tools'),
    ]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    icon_class = models.CharField(max_length=50, default="code", help_text="Material Icon name")

    def __str__(self):
        return self.name

# 2. STANDALONE JOBS DATABASE (For future Job Board)
class Job(models.Model):
    title = models.CharField(max_length=100)
    description = models.TextField()
    # In the future, we will link this to required skills
    # required_skills = models.ManyToManyField(Skill) 

    def __str__(self):
        return self.title

# 3. THE CONNECTOR (User selects a Skill + Sets Level)
class UserSkill(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    
    # The "Level" the user claims to have (1-10)
    level = models.IntegerField(default=1)
    
    # XP earned in this specific skill
    xp = models.IntegerField(default=0)
    
    class Meta:
        # Ensures a user can't add "Python" twice. They must update the existing one.
        unique_together = ('user', 'skill')

    def __str__(self):
        return f"{self.user.username} - {self.skill.name} (Lvl {self.level})"