from django.contrib import admin
from django.urls import path, include
from accounts.views import redirect_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("dashboard/", redirect_dashboard, name="dashboard"),
    path("", include("portfolio.urls")), 
    path("auth/", include("accounts.urls")), 
]
