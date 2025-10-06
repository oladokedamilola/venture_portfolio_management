# investments/admin.py
from django.contrib import admin
from .models import Investment

@admin.register(Investment)
class InvestmentAdmin(admin.ModelAdmin):
    list_display = (
        'investor',
        'startup',
        'amount',
        'equity',
        'valuation',
        'round',
        'investment_date',
        'status',
        'created_at'
    )
    list_filter = (
        'status',
        'round',
        'investment_date',
        'created_at'
    )
    search_fields = (
        'investor__username',
        'investor__email',
        'investor__first_name',
        'investor__last_name',
        'startup__name',
        'startup__description'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'investment_date'
    list_per_page = 20
    list_editable = ('status',)
    
    fieldsets = (
        ('Investment Parties', {
            'fields': (
                'investor',
                'startup'
            )
        }),
        ('Investment Details', {
            'fields': (
                'round',
                'investment_date',
                'status'
            )
        }),
        ('Financial Terms', {
            'fields': (
                'amount',
                'equity',
                'valuation'
            )
        }),
        ('Timestamps', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('investor', 'startup')
    
    def mark_as_exited(self, request, queryset):
        """Admin action to mark selected investments as exited"""
        updated = queryset.update(status='exited')
        self.message_user(request, f'{updated} investment(s) marked as exited.')
    mark_as_exited.short_description = "Mark selected investments as exited"
    
    def mark_as_written_off(self, request, queryset):
        """Admin action to mark selected investments as written off"""
        updated = queryset.update(status='written_off')
        self.message_user(request, f'{updated} investment(s) marked as written off.')
    mark_as_written_off.short_description = "Mark selected investments as written off"
    
    def mark_as_active(self, request, queryset):
        """Admin action to mark selected investments as active"""
        updated = queryset.update(status='active')
        self.message_user(request, f'{updated} investment(s) marked as active.')
    mark_as_active.short_description = "Mark selected investments as active"
    
    actions = [
        mark_as_exited,
        mark_as_written_off,
        mark_as_active
    ]
    
    def get_readonly_fields(self, request, obj=None):
        """Make financial fields read-only for non-active investments"""
        if obj and obj.status != 'active':
            # Once exited or written off, prevent editing of financial details
            return self.readonly_fields + ('amount', 'equity', 'valuation', 'round')
        return self.readonly_fields
    
    def investment_amount(self, obj):
        """Formatted amount for display"""
        return f"${obj.amount:,.2f}"
    investment_amount.short_description = 'Amount'
    
    def formatted_valuation(self, obj):
        """Formatted valuation for display"""
        return f"${obj.valuation:,.2f}"
    formatted_valuation.short_description = 'Valuation'