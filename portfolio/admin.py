from django.contrib import admin
from .models import Startup, Project, Task, FundingRound, Document

@admin.register(Startup)
class StartupAdmin(admin.ModelAdmin):
    list_display = ("name", "stage", "created_at")
    search_fields = ("name", "stage")

@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ("title", "startup", "deadline")
    search_fields = ("title", "startup__name")

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ("title", "project", "assigned_to", "status", "deadline")
    list_filter = ("status", "project__startup")
    search_fields = ("title", "project__title", "assigned_to__username")


@admin.register(FundingRound)
class FundingRoundAdmin(admin.ModelAdmin):
    list_display = ("startup", "round_type", "amount", "date")
    list_filter = ("round_type", "date")
    search_fields = ("startup__name",)

@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ("title", "startup", "uploaded_at")
    search_fields = ("title", "startup__name")

