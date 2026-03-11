from django.db import models
from django.conf import settings
from core.models import Skill

class Guild(models.Model):
    """The recruiter/company entity."""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    

    industry = models.CharField(max_length=100, default="Software Engineering", help_text="e.g., Fintech, Web3, Cybersec")
    minimum_level_to_join = models.PositiveIntegerField(default=1, help_text="Min player level required to apply/join")
    guild_xp = models.PositiveIntegerField(default=0, help_text="Total XP earned by members for the guild")
    is_verified = models.BooleanField(default=False, help_text="Grants the 'Verified' badge to trusted recruiters.")
        
    logo = models.ImageField(upload_to='guild_logos/', null=True, blank=True)
    founder = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='founded_guilds')
    members = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='guilds', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Quest(models.Model):
    """The Job Post / Bounty."""
    title = models.CharField(max_length=200)
    guild = models.ForeignKey(Guild, on_delete=models.CASCADE, related_name='quests')
    description = models.TextField()
    xp_reward = models.PositiveIntegerField(default=500, help_text="Bonus XP for landing this role")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} [{self.guild.name}]"

class QuestRequirement(models.Model):
    """The precise skills an applicant must prove to apply."""
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='requirements')
    skill = models.ForeignKey(Skill, on_delete=models.CASCADE)
    minimum_level = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"Lv.{self.minimum_level} {self.skill.name} for {self.quest.title}"
    
class QuestSubmission(models.Model):
    """Tracks players who accept a quest and their submitted code."""
    STATUS_CHOICES = (
        ('accepted', 'In Progress'),
        ('submitted', 'Under Review'),
        ('approved', 'Approved & Rewarded'),
        ('rejected', 'Rejected')
    )

    quest = models.ForeignKey(Quest, on_delete=models.CASCADE, related_name='submissions')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='quest_submissions')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='accepted')
    github_url = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('quest', 'user') # A player can only take a specific quest once

    def __str__(self):
        return f"{self.user.username} -> {self.quest.title} ({self.status})"