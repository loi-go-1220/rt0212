from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('history/', views.resume_history, name='resume_history'),
    path('resume/<int:pk>/', views.resume_detail, name='resume_detail'),
]
