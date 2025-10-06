# funding/urls.py
from django.urls import path
from . import views

app_name = 'funding'

urlpatterns = [
    # Founder URLs
    path('founder/funding/apply/', views.funding_apply, name='founder_funding_apply'),
    path('founder/funding/rounds/', views.funding_rounds, name='founder_funding_rounds'),
    
    # Manager URLs
    path('manager/funding/rounds/', views.manager_funding_rounds, name='manager_funding_rounds'),
    path('manager/funding/<int:pk>/', views.manager_funding_detail, name='manager_funding_detail'),
    path('manager/funding/<int:pk>/review/', views.manager_funding_review, name='manager_funding_review'),
    path('manager/funding/analytics/', views.funding_analytics, name='manager_funding_analytics'),
    
    # Generic URL (redirects based on role)
    path('funding/rounds/', views.funding_rounds, name='funding_rounds'),
    path('funding/analytics/', views.funding_analytics, name='funding_analytics'),
    
]