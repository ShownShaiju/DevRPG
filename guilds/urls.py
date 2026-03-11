from django.urls import path
from . import views

urlpatterns = [
    path('', views.guild_dashboard, name='guild_dashboard'),
    path('join/<int:guild_id>/', views.join_guild, name='join_guild'),
    path('leave/', views.leave_guild, name='leave_guild'),
    path('create/', views.create_guild, name='create_guild'),
    path('quests/', views.quest_board, name='quest_board'),
    
    path('quests/create/', views.create_quest, name='create_quest'),
    path('quests/<int:quest_id>/accept/', views.accept_quest, name='accept_quest'),
    path('quests/<int:quest_id>/submit/', views.submit_quest, name='submit_quest'),
    path('quests/submission/<int:submission_id>/approve/', views.approve_submission, name='approve_submission'),

]