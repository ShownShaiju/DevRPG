from django.urls import path
from . import views

urlpatterns = [
    path('dashboard/', views.dashboard, name='dashboard'),
    path('', views.index_redirect, name='index'),
    path('api/evaluation/start/', views.StartEvaluationView.as_view(), name='api-start-evaluation'),
    path('api/evaluation/session/<int:session_id>/submit/', views.SubmitAnswerView.as_view(), name='api-submit-answer'),
]