from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('login/', views.login_view, name='login'),
    path('profile/edit/', views.profile_edit, name='profile_edit'),
    path('skills/', views.skill_manager, name='skill_manager'),
    path('skills/delete/<int:pk>/', views.delete_skill, name='delete_skill'),
    path('api/avatar-status/', views.avatar_status, name='avatar_status'),
]