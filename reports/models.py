# reports/models.py
from django.db import models
from startups.models import Startup
from django.contrib.auth import get_user_model


CustomUser = get_user_model()

class Report(models.Model):
    REPORT_TYPE_CHOICES = [
        ('portfolio', 'Portfolio Report'),
        ('performance', 'Performance Report'),
        ('sector', 'Sector Analysis'),
        ('quarterly', 'Quarterly Review'),
    ]
    
    name = models.CharField(max_length=200)
    report_type = models.CharField(max_length=20, choices=REPORT_TYPE_CHOICES)
    generated_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.JSONField()  # Store report data as JSON
    file = models.FileField(upload_to='reports/', null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.name} - {self.get_report_type_display()}"