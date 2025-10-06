from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Startup(models.Model):
    STAGE_CHOICES = [
        ("IDEA", "Ideation"),
        ("MVP", "MVP Development"),
        ("FUNDING", "Fundraising"),
        ("SCALING", "Scaling"),
        ("EXIT", "Exit/Spin-off"),
    ]
    
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True, null=True)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES, default="IDEA")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.get_stage_display()})"


class Project(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="projects")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    deadline = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} - {self.startup.name}"


class Task(models.Model):
    STATUS_CHOICES = [
        ("TODO", "To Do"),
        ("IN_PROGRESS", "In Progress"),
        ("DONE", "Completed"),
    ]

    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name="tasks")
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="portfolio_tasks")
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="TODO")
    deadline = models.DateField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"


class FundingRound(models.Model):
    ROUND_TYPES = [
        ("SEED", "Seed"),
        ("SERIES_A", "Series A"),
        ("SERIES_B", "Series B"),
        ("SERIES_C", "Series C"),
        ("OTHER", "Other"),
    ]

    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="funding_rounds")
    round_type = models.CharField(max_length=20, choices=ROUND_TYPES, default="SEED")
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    date = models.DateField()

    def __str__(self):
        return f"{self.startup.name} - {self.get_round_type_display()} - ${self.amount}"


class Document(models.Model):
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name="documents")
    title = models.CharField(max_length=255)
    file = models.FileField(upload_to="documents/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} ({self.startup.name})"
