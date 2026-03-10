from django.urls import path
from . import views

urlpatterns = [
    path('', views.guild_dashboard, name='guild_dashboard'),
    path('join/<int:guild_id>/', views.join_guild, name='join_guild'),
    path('leave/', views.leave_guild, name='leave_guild'),
    path('create/', views.create_guild, name='create_guild'),
]