# accounts/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from .models import CustomUser

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ('username', 'email', 'get_full_name', 'role', 'department', 'is_active', 'email_verified')
    list_filter = ('role', 'department', 'is_active', 'email_verified', 'two_factor_enabled', 'is_staff')
    search_fields = ('username', 'email', 'first_name', 'last_name', 'department')
    ordering = ('-date_joined',)
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {
            'fields': (
                'first_name', 
                'last_name', 
                'email', 
                'phone', 
                'avatar', 
                'bio',
                'role',
                'department',
                'skills'
            )
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 
                'is_staff', 
                'is_superuser', 
                'groups', 
                'user_permissions',
                'email_verified',
                'two_factor_enabled'
            ),
        }),
        (_('Important dates'), {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'username', 
                'email', 
                'password1', 
                'password2', 
                'role',
                'is_active', 
                'is_staff'
            ),
        }),
    )
    
    readonly_fields = ('last_login', 'date_joined')
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = _('Full Name')
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Make role required in admin form
        form.base_fields['role'].required = True
        return form