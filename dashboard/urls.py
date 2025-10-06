# dashboard/urls.py
from django.urls import path
from . import views


urlpatterns = [    
    # Manager Dashboard
    path('manager/', views.manager_dashboard, name='manager_dashboard'),
    
    # Founder Dashboard  
    path('founder/', views.founder_dashboard, name='founder_dashboard'),
    
    # Team Member Dashboard
    path('team/', views.team_dashboard, name='team_dashboard'),
    
    # Investor Dashboard
    path('investor/', views.investor_dashboard, name='investor_dashboard'),
]