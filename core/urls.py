from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.index_redirect, name='index'),
    path('api/evaluation/start/', views.StartEvaluationView.as_view(), name='api-start-evaluation'),
    path('api/evaluation/session/<int:session_id>/submit/', views.SubmitAnswerView.as_view(), name='api-submit-answer'),
    path('api/evaluation/session/<int:session_id>/status/', views.CheckEvaluationStatusView.as_view(), name='api-check-status'),
    path('evaluate/', views.evaluation_room, name='evaluation_room'),
    path('hero/<str:username>/', views.dashboard, name='public_profile'),
    path('search/', views.search_view, name='search'),
    path('follow/<str:username>/', views.follow_toggle, name='follow_toggle'),
]