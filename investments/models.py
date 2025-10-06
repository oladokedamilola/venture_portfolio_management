# investments/models.py
from django.db import models
from django.utils import timezone
from startups.models import Startup
from django.contrib.auth import get_user_model

CustomUser = get_user_model()

class Investment(models.Model):
    ROUND_CHOICES = [
        ('pre_seed', 'Pre-Seed'),
        ('seed', 'Seed'),
        ('series_a', 'Series A'),
        ('series_b', 'Series B'),
        ('series_c', 'Series C+'),
    ]
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('exited', 'Exited'),
        ('written_off', 'Written Off'),
    ]
    
    investor = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='investments')
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='investments')
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    equity = models.FloatField(help_text="Equity percentage")
    valuation = models.DecimalField(max_digits=12, decimal_places=2, help_text="Post-money valuation")
    round = models.CharField(max_length=20, choices=ROUND_CHOICES)
    investment_date = models.DateField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Add the missing fields
    current_valuation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True, help_text="Current valuation for ROI calculation")
    exit_date = models.DateField(null=True, blank=True)
    exit_value = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.investor} - {self.startup} (${self.amount})"
    
    @property
    def current_value(self):
        """Calculate current value based on current valuation"""
        if self.current_valuation:
            ownership_percentage = self.equity / 100
            return float(self.current_valuation) * ownership_percentage
        return float(self.amount)  # Default to invested amount
    
    @property
    def current_roi(self):
        """Calculate current ROI percentage"""
        current_val = self.current_value
        return ((current_val - float(self.amount)) / float(self.amount)) * 100
    
    @property
    def is_overdue_update(self):
        """Check if investment needs update (older than 3 months)"""
        three_months_ago = timezone.now().date() - timezone.timedelta(days=90)
        return self.updated_at.date() < three_months_ago
    
    @property
    def days_since_investment(self):
        """Days since investment date"""
        return (timezone.now().date() - self.investment_date).days