from django.contrib import admin
from django.urls import path, include
from dashboard.views import dashboard_redirect
from accounts.views import profile_view
from django.conf import settings
from django.conf.urls.static import static
from . import views


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path('dashboard/', dashboard_redirect, name='dashboard_redirect'),
    path('my-profile/', profile_view, name='profile'),

    path("portfolio/", include("portfolio.urls")),
    path("auth/", include("accounts.urls")),
    path("projects/", include("projects.urls")),
    path("startups/", include("startups.urls")),
    path("reports/", include("reports.urls")),
    path("tasks/", include("tasks.urls")),
    path("communications/", include("communications.urls")),
    path("investments/", include("investments.urls")),
    path("funding/", include("funding.urls")),
    path("dashboard/", include("dashboard.urls")),
]

if settings.DEBUG:
    from django.conf import settings
    from django.conf.urls.static import static

    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)    
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
