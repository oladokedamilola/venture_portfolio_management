# # projects/admin.py
# from django.contrib import admin
# from .models import Project

# @admin.register(Project)
# class ProjectAdmin(admin.ModelAdmin):
#     list_display = (
#         'name',
#         'startup',
#         'status',
#         'priority',
#         'budget',
#         'progress_display',
#         'start_date',
#         'due_date',
#         'team_count',
#         'created_at'
#     )
#     list_filter = (
#         'status',
#         'priority',
#         'startup',
#         'start_date',
#         'due_date',
#         'created_at'
#     )
#     search_fields = (
#         'name',
#         'description',
#         'startup__name',
#         'team_members__username',
#         'team_members__first_name',
#         'team_members__last_name'
#     )
#     readonly_fields = ('created_at', 'updated_at', 'progress_display')
#     date_hierarchy = 'start_date'
#     list_per_page = 20
#     list_editable = ('status', 'priority')
#     filter_horizontal = ('team_members',)
    
#     fieldsets = (
#         ('Basic Information', {
#             'fields': (
#                 'name',
#                 'description',
#                 'startup'
#             )
#         }),
#         ('Project Details', {
#             'fields': (
#                 'status',
#                 'priority',
#                 'budget',
#                 'progress'
#             )
#         }),
#         ('Timeline', {
#             'fields': (
#                 'start_date',
#                 'due_date'
#             )
#         }),
#         ('Team', {
#             'fields': (
#                 'team_members',
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
#         return super().get_queryset(request).select_related('startup').prefetch_related('team_members')
    
#     def progress_display(self, obj):
#         """Display progress with percentage"""
#         return f"{obj.progress}%"
#     progress_display.short_description = 'Progress'
    
#     def team_count(self, obj):
#         """Display count of team members"""
#         return obj.team_members.count()
#     team_count.short_description = 'Team Size'
    
#     def mark_as_completed(self, request, queryset):
#         """Admin action to mark selected projects as completed"""
#         updated = queryset.update(status='completed', progress=100)
#         self.message_user(request, f'{updated} project(s) marked as completed.')
#     mark_as_completed.short_description = "Mark selected projects as completed"
    
#     def mark_as_in_progress(self, request, queryset):
#         """Admin action to mark selected projects as in progress"""
#         updated = queryset.update(status='in_progress')
#         self.message_user(request, f'{updated} project(s) marked as in progress.')
#     mark_as_in_progress.short_description = "Mark selected projects as in progress"
    
#     def set_high_priority(self, request, queryset):
#         """Admin action to set selected projects to high priority"""
#         updated = queryset.update(priority='high')
#         self.message_user(request, f'{updated} project(s) set to high priority.')
#     set_high_priority.short_description = "Set selected projects to high priority"
    
#     actions = [
#         mark_as_completed,
#         mark_as_in_progress,
#         set_high_priority
#     ]
    
#     def get_readonly_fields(self, request, obj=None):
#         """Make certain fields read-only based on status"""
#         if obj and obj.status == 'completed':
#             # Once completed, prevent editing of progress and dates
#             return self.readonly_fields + ('progress', 'start_date', 'due_date')
#         return self.readonly_fields
    
#     def budget_display(self, obj):
#         """Formatted budget for display"""
#         return f"${obj.budget:,.2f}"
#     budget_display.short_description = 'Budget'
    
#     def is_overdue(self, obj):
#         """Check if project is overdue"""
#         from django.utils import timezone
#         if obj.due_date and obj.status != 'completed':
#             return obj.due_date < timezone.now().date()
#         return False
#     is_overdue.boolean = True
#     is_overdue.short_description = 'Overdue'