from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    ROLE_CHOICES = [
        ("MANAGER", "Venture Manager"),
        ("FOUNDER", "Founder"),
        ("TEAM", "Team Member"),
        ("INVESTOR", "Investor"),
        ("STAFF", "Support Staff"),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="TEAM")

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"
