# funding/models.py
from django.db import models
from startups.models import Startup
from investments.models import Investment


class FundingApplication(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('funded', 'Funded'),
    ]
    
    startup = models.ForeignKey(Startup, on_delete=models.CASCADE, related_name='funding_applications')
    funding_round = models.CharField(max_length=20, choices=Investment.ROUND_CHOICES)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    equity_offered = models.FloatField(null=True, blank=True)
    valuation = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    
    # Application content
    pitch = models.TextField()
    use_of_funds = models.TextField()
    milestones = models.TextField()
    
    # Documents
    pitch_deck = models.FileField(upload_to='funding/pitch_decks/', null=True, blank=True)
    financials = models.FileField(upload_to='funding/financials/', null=True, blank=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.startup.name} - {self.get_funding_round_display()}"