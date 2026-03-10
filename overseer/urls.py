from django.urls import path
from . import views

urlpatterns = [
    path('', views.overseer_dashboard, name='overseer_dashboard'),
    path('guild/<int:guild_id>/verify/', views.toggle_guild_verification, name='overseer_verify_guild'),
    path('guild/<int:guild_id>/dismiss/', views.dismiss_guild, name='overseer_dismiss_guild'),
    path('player/<int:user_id>/wipe/', views.wipe_player_xp, name='overseer_wipe_xp'),
    path('player/<int:user_id>/ban/', views.toggle_player_ban, name='overseer_ban_player'),
]