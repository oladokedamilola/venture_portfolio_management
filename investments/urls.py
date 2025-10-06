# investments/urls.py
from django.urls import path
from . import views

app_name = 'investments'

urlpatterns = [
    path('dashboard/', views.investor_dashboard, name='investor_dashboard'),
    path('portfolio/', views.investor_portfolio, name='investor_portfolio'),
    path('funding/history/', views.funding_history, name='funding_history'),
    path('startups/', views.portfolio_startups, name='portfolio_startups'),
    path('reports/', views.investor_reports, name='investor_reports'),
    path('create/', views.investment_create, name='investment_create'),
    path('<int:pk>/edit/', views.investment_edit, name='investment_edit'),
    path('<int:pk>/', views.investment_detail, name='investment_detail'),
    path('<int:pk>/delete/', views.investment_delete, name='investment_delete'),
]