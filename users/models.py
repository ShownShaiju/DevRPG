from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import pre_save
from django.dispatch import receiver
from .tasks import delete_old_avatar_task

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
    
@receiver(pre_save, sender=Profile)
def delete_old_avatar_on_update(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old_profile = Profile.objects.get(pk=instance.pk)
    except Profile.DoesNotExist:
        return

    if old_profile.avatar_image and old_profile.avatar_image != instance.avatar_image:
        if old_profile.avatar_image.name != 'default.jpg':
            # Dispatch the file name to the Celery worker queue (.delay)
            # This takes less than 1 millisecond to execute
            delete_old_avatar_task.delay(old_profile.avatar_image.name)