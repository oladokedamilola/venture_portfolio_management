# accounts/urls.py
from django.urls import path
from django.contrib.auth import views as auth_views
from . import views


urlpatterns = [
    # Authentication URLs
    path('role-selection/', views.role_selection, name='role_selection'),
    path('register/', views.register, name='register'),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    
    # 📧 Email Verification
    # 1️⃣ Direct verification via link
    path("verify-email/", views.verify_email, name="verify_email"),
    # 2️⃣ Notice page (randomized: link or token)
    path("verify-email-notice/", views.verify_email_notice, name="verify_email_notice"),

    # 🔄 Password Reset
    path("password-reset/", views.password_reset_request, name="password_reset_request"),
    path("reset-password/<str:token>/", views.password_reset_confirm, name="password_reset_confirm"),
    
]