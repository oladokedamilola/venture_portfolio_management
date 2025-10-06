# projects/models.py
from django.db import models
from django.utils import timezone
from startups.models import Startup
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class Project(models.Model):
    STATUS_CHOICES = [
        ('not_started', 'Not Started'),
        ('in_progress', 'In Progress'),
        ('on_hold', 'On Hold'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    ]
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]
    
    name = models.CharField(max_length=200)
    description = models.TextField()
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='projects')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='not_started')
    priority = models.CharField(max_length=20, choices=PRIORITY_CHOICES, default='medium')
    budget = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    progress = models.IntegerField(default=0)

    # Timeline
    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    
    # REMOVED: team_members field
    # We'll add team members functionality later through a different approach
    
    # Track who created the project
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, 
                                 null=True, blank=True, related_name='created_projects')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.name} - {self.startup.name}"
    
    @property
    def days_remaining(self):
        """Calculate days remaining until due date"""
        if self.due_date:
            return (self.due_date - timezone.now().date()).days
        return None
    
    @property
    def is_overdue(self):
        """Check if project is overdue"""
        if self.due_date and self.status != 'completed':
            return self.days_remaining < 0
        return False