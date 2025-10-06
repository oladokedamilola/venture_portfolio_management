# reports/urls.py
from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    # Manager URLs
    path('manager/reports/', views.manager_reports, name='manager_reports'),
    path('manager/reports/generate/', views.generate_manager_report, name='generate_manager_report'),
    path('manager/reports/<int:pk>/', views.manager_report_detail, name='manager_report_detail'),
    path('manager/reports/quick-portfolio/', views.quick_portfolio_report, name='quick_portfolio_report'),
    path('manager/reports/project-performance/', views.project_performance_report, name='project_performance_report'),
    
    # Investor Reports (Read-only)
    path('investor/reports/', views.investor_reports, name='investor_reports'),
    path('investor/reports/generate/', views.generate_investor_report, name='generate_investor_report'),
    
    # Generic URLs
    path('<int:pk>/', views.report_detail, name='report_detail'),
    path('<int:pk>/download/', views.download_report, name='download_report'),
    path('<int:pk>/delete/', views.delete_report, name='delete_report'),
]