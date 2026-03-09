from django.urls import path
from . import views

urlpatterns = [
    path('', views.guild_dashboard, name='guild_dashboard'),
]