# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm  
from django.contrib.auth import get_user_model, authenticate


CustomUser = get_user_model()

class RoleSelectionForm(forms.Form):
    """Form for selecting role in the modal"""
    ROLE_CHOICES = [
        ('manager', 'Venture Manager'),
        ('founder', 'Founder'),
        ('team_member', 'Team Member'),
        ('investor', 'Investor'),
    ]
    
    role = forms.ChoiceField(
        choices=ROLE_CHOICES,
        widget=forms.RadioSelect,
        label="Select your role"
    )

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'first_name', 'last_name', 'phone', 'password1', 'password2')
        # Added 'username' back to fields
    
    def __init__(self, *args, **kwargs):
        # Get the selected role from kwargs
        self.selected_role = kwargs.pop('selected_role', None)
        super().__init__(*args, **kwargs)
        
        # Add Bootstrap classes to all fields
        for field_name, field in self.fields.items():
            field.widget.attrs.update({'class': 'form-control'})
            
        # Special handling for password fields
        self.fields['password1'].widget.attrs.update({'placeholder': 'Enter password'})
        self.fields['password2'].widget.attrs.update({'placeholder': 'Confirm password'})
        self.fields['username'].widget.attrs.update({'placeholder': 'Choose your username'})
        self.fields['email'].widget.attrs.update({'placeholder': 'your@email.com'})

    def save(self, commit=True):
        user = super().save(commit=False)
        # Set the role from the selected_role
        if self.selected_role:
            user.role = self.selected_role
        if commit:
            user.save()
        return user

class CustomAuthenticationForm(forms.Form):
    """Custom login form that accepts either email or username."""
    username = forms.CharField(
        label="Email or Username",
        widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username or Email"})
    )
    password = forms.CharField(
        label="Password",
        widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"})
    )

    def __init__(self, request=None, *args, **kwargs):
        self.request = request
        self.user_cache = None
        super().__init__(*args, **kwargs)

    def clean(self):
        username_or_email = self.cleaned_data.get("username")
        password = self.cleaned_data.get("password")

        if username_or_email and password:
            # Try authenticating directly with email first
            user = authenticate(self.request, email=username_or_email, password=password)

            # If that fails, try username-based lookup
            if user is None:
                try:
                    user_obj = CustomUser.objects.get(username=username_or_email)
                    user = authenticate(self.request, email=user_obj.email, password=password)
                except CustomUser.DoesNotExist:
                    user = None

            if user is None:
                raise forms.ValidationError("Invalid email/username or password.")
            
            self.user_cache = user

        return self.cleaned_data

    def get_user(self):
        return self.user_cache



class ProfileEditForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            'username', 'email', 'first_name', 'last_name', 
             'phone', 'avatar', 'bio', 'department', 'skills'
        ]
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Add Bootstrap classes to form fields
        for field in self.fields:
            if field != 'avatar':  # Don't add form-control to file input
                self.fields[field].widget.attrs.update({
                    'class': 'form-control',
                })

from django.contrib.auth.forms import SetPasswordForm

class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email", widget=forms.EmailInput(attrs={"placeholder": "Enter your email"}))

from django.contrib.auth.forms import SetPasswordForm

class PasswordResetForm(SetPasswordForm):
    """
    Standard Django SetPasswordForm with Bootstrap + IDs for JS validation.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Style and configure "New Password"
        self.fields["new_password1"].widget.attrs.update({
            "id": "id_password1",
            "class": "form-control",
            "placeholder": "Enter new password",
        })

        # Style and configure "Confirm Password"
        self.fields["new_password2"].widget.attrs.update({
            "id": "id_password2",
            "class": "form-control",
            "placeholder": "Confirm new password",
        })