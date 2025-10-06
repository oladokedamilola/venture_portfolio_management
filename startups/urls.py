# startups/urls.py
from django.urls import path
from . import views

app_name = 'startups'

urlpatterns = [
    # Generic URLs that work for all roles
    path('<int:pk>/edit/', views.startup_edit, name='startup_edit'),
    path('<int:pk>/delete/', views.startup_delete, name='startup_delete'),
    
    # Manager URLs
    path('manager/', views.manager_startup_list, name='manager_startup_list'),
    path('manager/dashboard/', views.manager_startup_dashboard, name='manager_startup_dashboard'),
    path('manager/create/', views.manager_startup_create, name='manager_startup_create'),
    path('manager/<int:pk>/', views.manager_startup_detail, name='manager_startup_detail'),
    path('manager/<int:pk>/edit/', views.startup_edit, name='manager_startup_edit'),
    path('manager/<int:pk>/delete/', views.startup_delete, name='manager_startup_delete'), 
    # Founder URLs  
    path('founder/', views.founder_startup_list, name='founder_startup_list'),
    path('founder/create/', views.founder_startup_create, name='founder_startup_create'),
    path('founder/<int:pk>/', views.founder_startup_detail, name='founder_startup_detail'),
    path('founder/<int:pk>/edit/', views.startup_edit, name='founder_startup_edit'),
    path('founder/<int:pk>/delete/', views.startup_delete, name='founder_startup_delete'),  
]