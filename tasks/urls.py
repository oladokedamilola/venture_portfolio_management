# tasks/urls.py
from django.urls import path
from . import views

app_name = 'tasks'

urlpatterns = [
    # Manager URLs
    path('manager/tasks/', views.task_list, name='manager_tasks'),
    path('manager/tasks/<int:pk>/', views.task_detail, name='manager_task_detail'),
    
    # Founder URLs
    path('founder/tasks/', views.task_list, name='founder_tasks'),
    path('founder/tasks/<int:pk>/', views.task_detail, name='founder_task_detail'),
    
    # Team Member URLs
    path('team/tasks/', views.task_list, name='team_tasks'),
    path('team/tasks/<int:pk>/', views.task_detail, name='team_task_detail'),
    path('team/tasks/<int:pk>/update/', views.task_update, name='team_task_update'),
]