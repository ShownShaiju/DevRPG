from django.apps import AppConfig
import time

class OverseerConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'overseer'
    
    boot_time = time.time()