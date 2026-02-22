from celery import shared_task
from PIL import Image, ImageOps
from .models import Profile

@shared_task
def optimize_avatar(profile_id):

    try:
        profile = Profile.objects.get(id=profile_id)
        
        if not profile.avatar_image or profile.avatar_image.name == 'default.jpg':
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
        profile=profile.objects.get(id=profile_id)
        profile.is_avatar_processing = False
        profile.save()
        return f"Task Failed: {str(e)}"