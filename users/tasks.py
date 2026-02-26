# users/tasks.py
from celery import shared_task
from PIL import Image, ImageOps
from .models import Profile
from django.core.files.storage import default_storage

@shared_task
def optimize_avatar(profile_id):
    try:
        # Use capital 'P' to query the database
        profile = Profile.objects.get(id=profile_id)
        
        # Enhanced Guard Clause: Skip if missing, default, or a web URL
        if not profile.avatar_image or \
           profile.avatar_image.name == 'default.jpg' or \
           profile.avatar_image.name.startswith('http'):
            
            profile.is_avatar_processing = False
            profile.save()
            return "No optimization required."

        img_path = profile.avatar_image.path
        img = Image.open(img_path)
        
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
            
        target_size = (300, 300) 
        img = ImageOps.fit(img, target_size, Image.Resampling.LANCZOS)
        img.save(img_path, format='JPEG', quality=85)
        
        profile.is_avatar_processing = False
        profile.save()
        
        return f"Avatar optimized successfully for Profile ID: {profile_id}"

    except Exception as e:
        # Failsafe: Ensure capital 'P' is used for Profile.objects
        failsafe_profile = Profile.objects.get(id=profile_id)
        failsafe_profile.is_avatar_processing = False
        failsafe_profile.save()
        return f"Task Failed: {str(e)}"
    
@shared_task
def delete_old_avatar_task(file_name):
    """
    Asynchronously deletes the orphaned file from storage.
    Accepts the file name as a string to prevent Celery serialization errors.
    """
    try:
        if default_storage.exists(file_name):
            default_storage.delete(file_name)
            return f"Garbage Collection: Successfully purged {file_name}"
        return f"Garbage Collection: File {file_name} already missing."
    except Exception as e:
        return f"Garbage Collection Failed: {str(e)}"    