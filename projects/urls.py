# projects/urls.py
from django.urls import path
from . import views

app_name = 'projects'

urlpatterns = [
    # Generic URLs
    path('', views.project_list, name='project_list'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('create/', views.project_create_edit, name='project_create'),
    path('<int:pk>/edit/', views.project_create_edit, name='project_edit'),

    path('projects/<int:pk>/archive/', views.project_archive, name='project_archive'),
    path('projects/<int:pk>/delete/', views.project_delete, name='project_delete'),
    
    # Manager-specific URLs
    path('manager/projects/', views.manager_projects, name='manager_projects'),
    path('manager/projects/<int:pk>/', views.manager_project_detail, name='manager_project_detail'),
    path('manager/projects/analytics/', views.manager_project_analytics, name='manager_project_analytics'),
    path('manager/projects/<int:pk>/archive/', views.project_archive, name='manager_project_archive'),
    path('manager/projects/<int:pk>/delete/', views.project_delete, name='manager_project_delete'),
    
    
    # Founder URLs
    path('founder/projects/', views.project_list, name='founder_projects'),
    path('founder/projects/<int:pk>/', views.project_detail, name='founder_project_detail'),
    path('founder/projects/<int:pk>/archive/', views.project_archive, name='founder_project_archive'),
    path('founder/projects/<int:pk>/delete/', views.project_delete, name='founder_project_delete'),
    
    
    # Team Member URLs
    path('team/projects/', views.project_list, name='team_projects'),
]