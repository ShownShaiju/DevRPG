from django.db import models
from django.contrib.auth.models import User

class Profile(models.Model):

    user = models.OneToOneField(User, on_delete=models.CASCADE)
    
    job_title = models.CharField(max_length=100, default="Novice Developer")
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=100, blank=True, default="Kerala, India")
    

    level = models.IntegerField(default=1)
    total_xp = models.IntegerField(default=0)
    
    avatar_image = models.ImageField(default='default.jpg', upload_to='profile_pics')
    is_avatar_processing = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.user.username}'s Profile"