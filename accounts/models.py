# accounts/models.py
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings
from datetime import timedelta


class CustomUser(AbstractUser):
    ROLE_CHOICES = [
        ('manager', 'Venture Manager'),
        ('founder', 'Founder'),
        ('team_member', 'Team Member'),
        ('investor', 'Investor'),
    ]
    
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='users/avatars/', null=True, blank=True)
    bio = models.TextField(blank=True)
    department = models.CharField(max_length=100, blank=True)
    skills = models.TextField(blank=True)

    # Verification and authentication
    email_verified = models.BooleanField(default=False)
    two_factor_enabled = models.BooleanField(default=False)

    # --- Email Verification Fields ---
    email_verification_token = models.CharField(max_length=128, blank=True, null=True)
    email_verification_expiry = models.DateTimeField(blank=True, null=True)
    last_verification_sent = models.DateTimeField(blank=True, null=True)
    verification_rate_limit_expiry = models.DateTimeField(blank=True, null=True)
    verification_request_count = models.IntegerField(default=0)

    # Use email as login field
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    # --- Email verification rate limiting ---
    def can_resend_verification(self) -> bool:
        now = timezone.now()

        # Hard cooldown
        if self.verification_rate_limit_expiry and now < self.verification_rate_limit_expiry:
            return False

        # Allow if fewer than 3 attempts in this window
        if self.verification_request_count < 3:
            # Enforce at least 1 minute between requests
            if self.last_verification_sent and (now - self.last_verification_sent).total_seconds() < 60:
                return False
            return True

        # If 3 attempts already used, enter cooldown
        return False

    def mark_verification_sent(self):
        now = timezone.now()

        # Reset tracking if cooldown expired
        if self.verification_rate_limit_expiry and now >= self.verification_rate_limit_expiry:
            self.verification_request_count = 0
            self.verification_rate_limit_expiry = None

        self.last_verification_sent = now
        self.verification_request_count += 1

        # Enforce cooldown after 3rd request
        if self.verification_request_count >= 3:
            self.verification_rate_limit_expiry = now + timedelta(hours=1)
            self.verification_request_count = 0

        self.save(update_fields=[
            "last_verification_sent",
            "verification_request_count",
            "verification_rate_limit_expiry",
        ])

    # --- Email verification alias (backward-compatible) ---
    @property
    def is_email_verified(self):
        """Alias for backward compatibility"""
        return self.email_verified

    @is_email_verified.setter
    def is_email_verified(self, value: bool):
        """Allow assignment to alias"""
        self.email_verified = value



# ---------------------------
# 🔐 EMAIL VERIFICATION TOKEN
# ---------------------------
class EmailVerificationToken(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_tokens')
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def __str__(self):
        return f"Token for {self.user.email} (Used: {self.used})"

    def is_valid(self):
        return not self.used and self.expires_at > timezone.now()


# ---------------------------
# 🔁 PASSWORD RESET SYSTEM
# ---------------------------
class PasswordResetToken(models.Model):
    user = models.ForeignKey("CustomUser", on_delete=models.CASCADE, related_name="reset_tokens")
    token = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    used = models.BooleanField(default=False)

    def is_expired(self):
        """Check if this token has expired based on current time or marked as used."""
        return self.used or timezone.now() > self.expires_at

    def __str__(self):
        return f"PasswordResetToken({self.user.email}, expired={self.is_expired()})"


class PasswordResetAttempt(models.Model):
    """
    Tracks password reset requests to prevent spam or brute-force attacks.
    Each user can only request a limited number of resets per time period.
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='password_reset_attempts')
    timestamp = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    successful = models.BooleanField(default=False)

    def __str__(self):
        status = "Successful" if self.successful else "Attempted"
        return f"{status} reset by {self.user.email} at {self.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

    @classmethod
    def recent_attempts(cls, user, minutes=10):
        cutoff = timezone.now() - timezone.timedelta(minutes=minutes)
        return cls.objects.filter(user=user, timestamp__gte=cutoff)

    @classmethod
    def too_many_attempts(cls, user, limit=3, minutes=10):
        return cls.recent_attempts(user, minutes=minutes).count() >= limit


# ---------------------------
# 🕒 EMAIL COOLDOWN TRACKER
# ---------------------------
class EmailCooldown(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='email_cooldown')
    last_sent = models.DateTimeField(auto_now=True)

    def can_send(self, cooldown_seconds=60):
        """Check if user can send another verification email"""
        if not self.last_sent:
            return True
        return (timezone.now() - self.last_sent).total_seconds() > cooldown_seconds
