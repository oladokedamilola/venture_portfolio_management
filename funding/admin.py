# funding/admin.py
from django.contrib import admin
from .models import FundingApplication

@admin.register(FundingApplication)
class FundingApplicationAdmin(admin.ModelAdmin):
    list_display = (
        'startup', 
        'funding_round', 
        'amount', 
        'equity_offered', 
        'valuation', 
        'status', 
        'created_at'
    )
    list_filter = (
        'status', 
        'funding_round', 
        'created_at', 
        'updated_at'
    )
    search_fields = (
        'startup__name',
        'startup__description',
        'pitch',
        'use_of_funds',
        'milestones'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 20
    list_editable = ('status',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'startup', 
                'funding_round', 
                'status'
            )
        }),
        ('Financial Details', {
            'fields': (
                'amount', 
                'equity_offered', 
                'valuation'
            )
        }),
        ('Application Content', {
            'fields': (
                'pitch', 
                'use_of_funds', 
                'milestones'
            )
        }),
        ('Documents', {
            'fields': (
                'pitch_deck', 
                'financials'
            ),
            'classes': ('collapse',)
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
        return super().get_queryset(request).select_related('startup')
    
    def change_status_to_approved(self, request, queryset):
        """Admin action to approve selected funding applications"""
        updated = queryset.update(status='approved')
        self.message_user(request, f'{updated} funding application(s) approved.')
    change_status_to_approved.short_description = "Approve selected applications"
    
    def change_status_to_rejected(self, request, queryset):
        """Admin action to reject selected funding applications"""
        updated = queryset.update(status='rejected')
        self.message_user(request, f'{updated} funding application(s) rejected.')
    change_status_to_rejected.short_description = "Reject selected applications"
    
    def change_status_to_under_review(self, request, queryset):
        """Admin action to mark selected applications as under review"""
        updated = queryset.update(status='under_review')
        self.message_user(request, f'{updated} funding application(s) marked as under review.')
    change_status_to_under_review.short_description = "Mark selected as under review"
    
    actions = [
        change_status_to_approved,
        change_status_to_rejected,
        change_status_to_under_review
    ]
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only based on status"""
        if obj and obj.status in ['approved', 'rejected', 'funded']:
            # Once approved/rejected/funded, prevent editing of financial details
            return self.readonly_fields + ('amount', 'equity_offered', 'valuation', 'funding_round')
        return self.readonly_fields