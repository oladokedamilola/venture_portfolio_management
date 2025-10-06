# # startups/admin.py
# from django.contrib import admin
# from django.utils.html import format_html
# from .models import Startup

# @admin.register(Startup)
# class StartupAdmin(admin.ModelAdmin):
#     list_display = (
#         'name',
#         'logo_display',
#         'industry_display',
#         'stage_display',
#         'location',
#         'team_size',
#         'monthly_revenue_display',
#         'valuation_display',
#         'founding_date',
#         'founder_count',
#         'created_at'
#     )
#     list_filter = (
#         'industry',
#         'stage',
#         'founding_date',
#         'created_at',
#         'team_size'
#     )
#     search_fields = (
#         'name',
#         'description',
#         'location',
#         'market',
#         'founders__username',
#         'founders__first_name',
#         'founders__last_name'
#     )
#     readonly_fields = ('created_at', 'updated_at', 'logo_preview')
#     date_hierarchy = 'founding_date'
#     list_per_page = 20
#     filter_horizontal = ('founders',)
    
#     fieldsets = (
#         ('Basic Information', {
#             'fields': (
#                 'name',
#                 'description',
#                 'logo',
#                 'logo_preview',
#                 'website'
#             )
#         }),
#         ('Business Details', {
#             'fields': (
#                 'industry',
#                 'stage',
#                 'founding_date',
#                 'location',
#                 'team_size',
#                 'market'
#             )
#         }),
#         ('Financial Metrics', {
#             'fields': (
#                 'monthly_revenue',
#                 'valuation'
#             )
#         }),
#         ('Team', {
#             'fields': (
#                 'founders',
#             )
#         }),
#         ('Metadata', {
#             'fields': (
#                 'created_at',
#                 'updated_at'
#             ),
#             'classes': ('collapse',)
#         })
#     )
    
#     def get_queryset(self, request):
#         return super().get_queryset(request).prefetch_related('founders')
    
#     def logo_display(self, obj):
#         """Display logo thumbnail in list view"""
#         if obj.logo:
#             return format_html(
#                 '<img src="{}" width="50" height="50" style="border-radius: 5px; object-fit: cover;" />',
#                 obj.logo.url
#             )
#         return "—"
#     logo_display.short_description = 'Logo'
    
#     def logo_preview(self, obj):
#         """Display logo preview in detail view"""
#         if obj.logo:
#             return format_html(
#                 '<img src="{}" width="100" height="100" style="border-radius: 5px; object-fit: cover; border: 1px solid #ddd;" />',
#                 obj.logo.url
#             )
#         return "No logo uploaded"
#     logo_preview.short_description = 'Logo Preview'
#     logo_preview.allow_tags = True
    
#     def industry_display(self, obj):
#         """Display formatted industry"""
#         return obj.get_industry_display()
#     industry_display.short_description = 'Industry'
    
#     def stage_display(self, obj):
#         """Display formatted stage"""
#         return obj.get_stage_display()
#     stage_display.short_description = 'Stage'
    
#     def monthly_revenue_display(self, obj):
#         """Formatted monthly revenue"""
#         return f"${obj.monthly_revenue:,.2f}"
#     monthly_revenue_display.short_description = 'Monthly Revenue'
    
#     def valuation_display(self, obj):
#         """Formatted valuation"""
#         return f"${obj.valuation:,.2f}"
#     valuation_display.short_description = 'Valuation'
    
#     def founder_count(self, obj):
#         """Display count of founders"""
#         return obj.founders.count()
#     founder_count.short_description = 'Founders'
    
#     def mark_as_growth_stage(self, request, queryset):
#         """Admin action to mark selected startups as growth stage"""
#         updated = queryset.update(stage='growth')
#         self.message_user(request, f'{updated} startup(s) marked as growth stage.')
#     mark_as_growth_stage.short_description = "Mark selected as growth stage"
    
#     def mark_as_series_a(self, request, queryset):
#         """Admin action to mark selected startups as Series A"""
#         updated = queryset.update(stage='series_a')
#         self.message_user(request, f'{updated} startup(s) marked as Series A.')
#     mark_as_series_a.short_description = "Mark selected as Series A"
    
#     def update_team_size(self, request, queryset):
#         """Admin action to update team size based on founders count"""
#         for startup in queryset:
#             startup.team_size = max(startup.founders.count(), startup.team_size)
#             startup.save()
#         self.message_user(request, f'Team size updated for {queryset.count()} startup(s).')
#     update_team_size.short_description = "Update team size from founders"
    
#     actions = [
#         mark_as_growth_stage,
#         mark_as_series_a,
#         update_team_size
#     ]
    
#     def get_readonly_fields(self, request, obj=None):
#         """Make certain fields read-only for older startups"""
#         if obj and obj.founding_date and obj.founding_date.year < 2020:
#             # For startups founded before 2020, prevent editing of founding date and stage
#             return self.readonly_fields + ('founding_date', 'stage')
#         return self.readonly_fields
    
#     def is_early_stage(self, obj):
#         """Check if startup is in early stage"""
#         return obj.stage in ['idea', 'pre_seed', 'seed']
#     is_early_stage.boolean = True
#     is_early_stage.short_description = 'Early Stage'
    
#     def save_model(self, request, obj, form, change):
#         """Ensure team size is at least the number of founders"""
#         if obj.founders.exists():
#             obj.team_size = max(obj.team_size, obj.founders.count())
#         super().save_model(request, obj, form, change)