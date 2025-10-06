from django.db import models
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


class Startup(models.Model):
    INDUSTRY_CHOICES = [
        ('tech', 'Technology'),
        ('healthcare', 'Healthcare'),
        ('finance', 'Finance'),
        ('education', 'Education'),
        ('ecommerce', 'E-commerce'),
        ('other', 'Other'),
    ]

    STAGE_CHOICES = [
        ('idea', 'Idea Stage'),
        ('pre_seed', 'Pre-Seed'),
        ('seed', 'Seed'),
        ('series_a', 'Series A'),
        ('series_b', 'Series B'),
        ('growth', 'Growth Stage'),
    ]

    name = models.CharField(max_length=200)
    description = models.TextField()
    industry = models.CharField(max_length=20, choices=INDUSTRY_CHOICES)
    stage = models.CharField(max_length=20, choices=STAGE_CHOICES)
    founding_date = models.DateField()
    website = models.URLField(blank=True)
    logo = models.ImageField(upload_to='startups/logos/', null=True, blank=True)
    location = models.CharField(max_length=100)
    team_size = models.IntegerField(default=1)
    market = models.TextField()
    is_active = models.BooleanField(default=True)

    # Financial metrics
    monthly_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    valuation = models.DecimalField(max_digits=12, decimal_places=2, default=0)

    # Founder (automatically assigned in the view)
    founder = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='founded_startups'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
