from django.urls import path
from . import views

urlpatterns = [
    path("startups/", views.startup_list, name="startup_list"),
    path("startup/<int:pk>/", views.startup_detail, name="startup_detail"),
    path("startup/create/", views.startup_create, name="startup_create"),
    path("startup/<int:pk>/edit/", views.startup_edit, name="startup_edit"),
    path("startup/<int:pk>/delete/", views.startup_delete, name="startup_delete"),

    path("project/create/", views.project_create, name="project_create"),
    path("task/create/", views.task_create, name="task_create"),
    path("funding/create/", views.funding_create, name="funding_create"),
]
