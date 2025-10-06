from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction, IntegrityError
from django.utils import timezone
from django.urls import reverse
from datetime import timedelta

# Local imports
from .models import CustomUser, PasswordResetToken, PasswordResetAttempt
from .forms import (
    RoleSelectionForm, CustomUserCreationForm, CustomAuthenticationForm,
    PasswordResetRequestForm, PasswordResetForm, ProfileEditForm
)
from .utils import (
    send_verification_email, verify_email_token,
    generate_password_reset_token, send_password_reset_email
)
from django.conf import settings

# ----------------------------
# 🧩 Role Selection
# ----------------------------
def role_selection(request):
    if request.method == 'POST':
        role = request.POST.get('role')
        if role in ['manager', 'founder', 'team_member', 'investor']:
            request.session['selected_role'] = role
            return redirect('register')
        else:
            messages.error(request, 'Please select a valid role.')
    return redirect('home')


# ----------------------------
# 🔐 Registration (with email verification)
# ----------------------------
def register(request):
    selected_role = request.session.get('selected_role')
    if not selected_role:
        messages.info(request, 'Please select your role first.')
        return redirect('role_selection')

    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST, selected_role=selected_role)
        try:
            if form.is_valid():
                with transaction.atomic():
                    user = form.save(commit=False)
                    user.role = selected_role.upper()
                    user.is_email_verified = False
                    user.save()

                    send_verification_email(user, request)
                    auth_login(request, user)

                    del request.session['selected_role']
                    messages.success(request, "✅ Welcome! Please check your email to verify your account.")
                    return redirect('verify_email_notice')
            else:
                messages.error(request, '❌ Please correct the errors below.')
        except IntegrityError:
            messages.error(request, '⚠️ A user with this email already exists.')
        except Exception as e:
            messages.error(request, f'⚠️ Unexpected error: {str(e)}')
    else:
        form = CustomUserCreationForm(selected_role=selected_role)

    return render(request, 'auth/register.html', {
        'form': form,
        'selected_role': selected_role,
        'role_display': dict(CustomUser.ROLE_CHOICES).get(selected_role)
    })


# ----------------------------
# ✉ Email Verification
# ----------------------------
@login_required
def verify_email_notice(request):
    """
    Handles the user-facing email verification page:
    - Shows current verification method (token/link)
    - Allows resending email if not rate-limited
    - Verifies user manually if token method is used
    """
    user = request.user

    # ✅ Already verified
    if user.is_email_verified:
        messages.success(request, "✅ Your email is already verified.")
        return redirect('dashboard_redirect')

    # ✅ Check cooldown period
    if user.verification_rate_limit_expiry and user.verification_rate_limit_expiry > timezone.now():
        remaining = (user.verification_rate_limit_expiry - timezone.now()).total_seconds()
        if remaining > 60:
            return render(request, "auth/verification_cooldown.html", {"user": user})

    # ✅ Determine current verification method
    method = request.session.get("email_verification_method")
    if not method:
        method = send_verification_email(user, request)
        if not method:
            messages.error(request, "⚠️ Could not send verification email. Please try again later.")
            return redirect('dashboard_redirect')
        request.session["email_verification_method"] = method

    token_for_display = user.email_verification_token
    verification_link = None

    # ✅ Handle resend request
    if request.method == "POST" and "resend" in request.POST:
        if not user.can_resend_verification():
            return render(request, "auth/verification_cooldown.html", {"user": user})
        sent_method = send_verification_email(user, request, method=method)
        if sent_method:
            messages.success(request, f"📧 A new verification {sent_method} has been sent to your email.")
        else:
            messages.warning(request, "⚠️ Please wait before requesting another email.")
        return redirect("verify_email_notice")

    # ✅ Handle token verification
    elif request.method == "POST" and method == "token":
        submitted_token = request.POST.get("token", "").strip()
        if not submitted_token:
            messages.error(request, "❌ Please enter the token sent to your email.")
        elif verify_email_token(submitted_token, user.email):
            messages.success(request, "✅ Your email has been verified successfully!")
            request.session.pop("email_verification_method", None)
            return redirect('dashboard_redirect')
        else:
            messages.error(request, "❌ Invalid or expired token. Please try again or resend a new one.")

    # ✅ Prepare data for template
    if method == "link" and token_for_display:
        verification_link = request.build_absolute_uri(
            reverse("verify_email") + f"?token={token_for_display}&email={user.email}"
        )

    return render(request, "auth/verify_email.html", {
        "user": user,
        "method": method,
        "token_for_display": token_for_display if method == "token" else None,
        "verification_link": verification_link if method == "link" else None,
        "show_resend": True,
    })


def verify_email(request):
    """
    Handles direct link-based verification.
    Example URL: /auth/verify-email/?token=123456&email=test@example.com
    """
    token = request.GET.get("token")
    email = request.GET.get("email")

    if not token or not email:
        messages.error(request, "❌ Invalid verification link.")
        return redirect("login")

    # ✅ Attempt verification
    verified = verify_email_token(token, email)
    if verified:
        messages.success(request, "✅ Your email has been verified successfully! You can now log in.")
    else:
        messages.error(request, "❌ Verification failed or link has expired. Please log in and request a new one.")

    return redirect("login")

# ----------------------------
# 🔄 Password Reset
# ----------------------------
RESET_LIMIT = 3
RESET_WINDOW_MINUTES = 30

def password_reset_request(request):
    """
    Handle password reset requests:
    - Protect against enumeration by returning the same success message whether the email exists or not.
    - Rate-limit requests per user using PasswordResetAttempt.recent_attempts.
    - Create a PasswordResetToken with an expires_at timestamp.
    - Log the attempt (with client IP) in PasswordResetAttempt.
    """
    if request.method == "POST":
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data["email"].lower()

            # Look up user but do NOT leak whether they exist
            user = CustomUser.objects.filter(email=email).first()

            # If user does not exist, still show the same success message (prevents enumeration)
            if not user:
                messages.success(
                    request,
                    "✅ If an account exists with that email, we’ve sent a password reset link. Please check your inbox."
                )
                return redirect("login")

            # Determine number of recent attempts (recent_attempts may return an int or a QuerySet)
            attempts_raw = PasswordResetAttempt.recent_attempts(user, minutes=RESET_WINDOW_MINUTES)
            if hasattr(attempts_raw, "count"):
                attempts_count = attempts_raw.count()
            else:
                try:
                    attempts_count = int(attempts_raw)
                except Exception:
                    # Fallback if it's an iterable
                    attempts_count = len(attempts_raw) if hasattr(attempts_raw, "__len__") else 0

            if attempts_count >= RESET_LIMIT:
                messages.error(
                    request,
                    f"⚠️ Maximum {RESET_LIMIT} reset attempts allowed in {RESET_WINDOW_MINUTES} minutes. Try later."
                )
                return redirect("password_reset_request")

            # Log the password reset attempt (include IP when available)
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip = x_forwarded_for.split(",")[0].strip()
            else:
                ip = request.META.get("REMOTE_ADDR")
            PasswordResetAttempt.objects.create(user=user, ip_address=ip, successful=False)

            # Generate token and expiry, save it
            token = generate_password_reset_token()
            expiry_hours = getattr(settings, "PASSWORD_RESET_TOKEN_EXPIRY_HOURS", 1)
            expires_at = timezone.now() + timedelta(hours=expiry_hours)
            PasswordResetToken.objects.create(user=user, token=token, expires_at=expires_at)

            # Send email (do not raise to user — still return generic message)
            try:
                send_password_reset_email(user, token, request=request)
            except Exception as e:
                # Keep this non-fatal — log for debugging
                print(f"⚠️ Could not send password reset email to {user.email}: {e}")

            messages.success(
                request,
                "✅ If an account exists with that email, we’ve sent a password reset link. Please check your inbox."
            )
            return redirect("login")
    else:
        form = PasswordResetRequestForm()

    return render(request, "auth/password_reset_request.html", {"form": form})



def password_reset_confirm(request, token):
    reset_token = get_object_or_404(PasswordResetToken, token=token, used=False)
    if reset_token.is_expired():
        messages.error(request, "❌ This reset link has expired.")
        return redirect("password_reset_request")

    if request.method == "POST":
        form = PasswordResetForm(reset_token.user, request.POST)
        if form.is_valid():
            form.save()
            reset_token.used = True
            reset_token.save()
            messages.success(request, "✅ Password reset successful.")
            return redirect("login")
    else:
        form = PasswordResetForm(reset_token.user)

    return render(request, "auth/password_reset_confirm.html", {"form": form})


# ----------------------------
# 🔑 Login & Logout
# ----------------------------
def custom_login(request):
    """
    Safe login view:
    - Avoids AttributeError when authentication fails (user is None)
    - Simple session-based throttle (max attempts -> temporary lockout)
    - Allows unverified users to log in so they can reach verify_email_notice
    """
    from django.utils import timezone

    if request.user.is_authenticated:
        return redirect('dashboard_redirect')

    # Simple session-based throttling
    ATTEMPS_KEY = "login_attempts"
    LOCKOUT_KEY = "login_lockout_until"
    MAX_ATTEMPTS = 5
    LOCKOUT_SECONDS = 300  # 5 minutes

    # Check lockout
    lockout_until_ts = request.session.get(LOCKOUT_KEY)
    if lockout_until_ts:
        try:
            now_ts = timezone.now().timestamp()
            if now_ts < float(lockout_until_ts):
                remaining = int(float(lockout_until_ts) - now_ts)
                messages.error(request, f"Too many failed login attempts. Try again in {remaining} second(s).")
                return render(request, 'auth/login.html', {'form': CustomAuthenticationForm()})
            else:
                # expired -> clear
                request.session.pop(LOCKOUT_KEY, None)
                request.session.pop(ATTEMPS_KEY, None)
        except Exception:
            # if something odd in session, clear it
            request.session.pop(LOCKOUT_KEY, None)
            request.session.pop(ATTEMPS_KEY, None)

    if request.method == 'POST':
        form = CustomAuthenticationForm(request, data=request.POST)
        if form.is_valid():
            user = form.get_user()

            # Defensive: form should provide a user, but guard anyway
            if user is None:
                # increment attempts and show generic error
                attempts = request.session.get(ATTEMPS_KEY, 0) + 1
                request.session[ATTEMPS_KEY] = attempts
                if attempts >= MAX_ATTEMPTS:
                    request.session[LOCKOUT_KEY] = timezone.now().timestamp() + LOCKOUT_SECONDS
                    messages.error(request, "Too many failed login attempts. Try again later.")
                else:
                    messages.error(request, "Invalid credentials. Please try again.")
                return render(request, 'auth/login.html', {'form': form})

            # Successful authentication -> clear attempts
            request.session.pop(ATTEMPS_KEY, None)
            request.session.pop(LOCKOUT_KEY, None)

            # If email not verified: allow login (so user can see verification notice)
            if not getattr(user, 'is_email_verified', False):
                # make sure auth_login is available (import at top of file: `from django.contrib.auth import login as auth_login`)
                auth_login(request, user)
                messages.warning(request, "⚠️ Your email is not verified. Please check your inbox.")
                return redirect("verify_email_notice")

            # Normal verified-user login
            auth_login(request, user)
            messages.success(request, f'Welcome back, {user.first_name or user.username}!')
            next_url = request.GET.get('next')
            if next_url:
                return redirect(next_url)
            return redirect('dashboard_redirect')

        else:
            # Invalid form -> increment attempts (don't leak whether user exists)
            attempts = request.session.get(ATTEMPS_KEY, 0) + 1
            request.session[ATTEMPS_KEY] = attempts
            if attempts >= MAX_ATTEMPTS:
                request.session[LOCKOUT_KEY] = timezone.now().timestamp() + LOCKOUT_SECONDS
                messages.error(request, "Too many failed login attempts. Try again in 5 minutes.")
            else:
                messages.error(request, 'Invalid username/email or password.')
    else:
        form = CustomAuthenticationForm()

    return render(request, 'auth/login.html', {'form': form})



@login_required
def custom_logout(request):
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('login')



# ----------------------------
# 👤 Profile Views (Single Page)
# ----------------------------
# views.py
@login_required
def profile_view(request):
    user = request.user
    print(f"DEBUG: User: {user}")  # Check if user is available
    print(f"DEBUG: User authenticated: {user.is_authenticated}")
    
    # Handle form submission
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Profile updated successfully!')
            return redirect('profile')
        else:
            messages.error(request, 'Please correct the errors below.')
            print(f"DEBUG: Form errors: {form.errors}")  # Check form errors
    else:
        form = ProfileEditForm(instance=user)
        print(f"DEBUG: Form created with instance: {user}")
    
    context = {
        'user': user,
        'form': form,
        'debug': True  # Add debug flag
    }
    return render(request, 'profile.html', context)


