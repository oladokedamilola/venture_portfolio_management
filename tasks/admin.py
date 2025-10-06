# tasks/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import Task

@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'project',
        'assigned_to',
        'status_display',
        'priority_display',
        'progress_display',
        'due_date',
        'is_overdue',
        'created_at'
    )
    list_filter = (
        'status',
        'priority',
        'project',
        'assigned_to',
        'due_date',
        'created_at'
    )
    search_fields = (
        'title',
        'description',
        'project__name',
        'assigned_to__username',
        'assigned_to__first_name',
        'assigned_to__last_name'
    )
    readonly_fields = ('created_at', 'updated_at', 'progress_display', 'is_overdue_display')
    date_hierarchy = 'due_date'
    list_per_page = 25
    list_editable = ()
    
    fieldsets = (
        ('Basic Information', {
            'fields': (
                'title',
                'description',
                'project'
            )
        }),
        ('Task Details', {
            'fields': (
                'status',
                'priority',
                'progress',
                'progress_display'
            )
        }),
        ('Assignment', {
            'fields': (
                'assigned_to',
                'due_date',
                'is_overdue_display'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
                'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('project', 'assigned_to')
    
    def status_display(self, obj):
        """Display formatted status with color coding"""
        status_colors = {
            'not_started': '#6b7280',  # gray
            'in_progress': '#3b82f6',   # blue
            'review': '#f59e0b',        # amber
            'completed': '#10b981',     # green
            'blocked': '#ef4444',       # red
        }
        color = status_colors.get(obj.status, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_display.short_description = 'Status'
    
    def priority_display(self, obj):
        """Display formatted priority with color coding"""
        priority_colors = {
            'low': '#10b981',    # green
            'medium': '#f59e0b', # amber
            'high': '#ef4444',   # red
        }
        color = priority_colors.get(obj.priority, '#6b7280')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_priority_display()
        )
    priority_display.short_description = 'Priority'
    
    def progress_display(self, obj):
        """Display progress with bar and percentage"""
        color = '#10b981' if obj.progress == 100 else '#3b82f6'  # green if complete, blue otherwise
        return format_html(
            '<div style="width: 100px; background: #e5e7eb; border-radius: 10px; height: 20px; position: relative;">'
            '<div style="width: {}%; background: {}; height: 100%; border-radius: 10px;"></div>'
            '<span style="position: absolute; top: 0; left: 0; width: 100%; text-align: center; '
            'font-size: 12px; font-weight: bold; color: {}; line-height: 20px;">{}%</span>'
            '</div>',
            obj.progress, color, 'white' if obj.progress > 50 else '#374151', obj.progress
        )
    progress_display.short_description = 'Progress'
    
    def is_overdue(self, obj):
        """Check if task is overdue in list view"""
        if obj.due_date and obj.status != 'completed':
            return obj.due_date < timezone.now().date()
        return False
    is_overdue.boolean = True
    is_overdue.short_description = 'Overdue'
    
    def is_overdue_display(self, obj):
        """Display overdue status in detail view"""
        if obj.due_date and obj.status != 'completed':
            if obj.due_date < timezone.now().date():
                days_overdue = (timezone.now().date() - obj.due_date).days
                return format_html(
                    '<span style="color: #ef4444; font-weight: bold;">⚠️ Overdue by {} days</span>',
                    days_overdue
                )
        return format_html('<span style="color: #10b981;">✓ On track</span>')
    is_overdue_display.short_description = 'Due Status'
    is_overdue_display.allow_tags = True
    
    def mark_as_completed(self, request, queryset):
        """Admin action to mark selected tasks as completed"""
        updated = queryset.update(status='completed', progress=100)
        self.message_user(request, f'{updated} task(s) marked as completed.')
    mark_as_completed.short_description = "Mark selected tasks as completed"
    
    def mark_as_in_progress(self, request, queryset):
        """Admin action to mark selected tasks as in progress"""
        updated = queryset.update(status='in_progress')
        self.message_user(request, f'{updated} task(s) marked as in progress.')
    mark_as_in_progress.short_description = "Mark selected tasks as in progress"
    
    def set_high_priority(self, request, queryset):
        """Admin action to set selected tasks to high priority"""
        updated = queryset.update(priority='high')
        self.message_user(request, f'{updated} task(s) set to high priority.')
    set_high_priority.short_description = "Set selected tasks to high priority"
    
    def update_progress_25(self, request, queryset):
        """Admin action to set progress to 25%"""
        updated = queryset.update(progress=25, status='in_progress')
        self.message_user(request, f'{updated} task(s) progress set to 25%.')
    update_progress_25.short_description = "Set progress to 25%"
    
    def update_progress_50(self, request, queryset):
        """Admin action to set progress to 50%"""
        updated = queryset.update(progress=50, status='in_progress')
        self.message_user(request, f'{updated} task(s) progress set to 50%.')
    update_progress_50.short_description = "Set progress to 50%"
    
    def update_progress_75(self, request, queryset):
        """Admin action to set progress to 75%"""
        updated = queryset.update(progress=75, status='in_progress')
        self.message_user(request, f'{updated} task(s) progress set to 75%.')
    update_progress_75.short_description = "Set progress to 75%"
    
    actions = [
        mark_as_completed,
        mark_as_in_progress,
        set_high_priority,
        update_progress_25,
        update_progress_50,
        update_progress_75,
    ]
    
    def get_readonly_fields(self, request, obj=None):
        """Make certain fields read-only for completed tasks"""
        if obj and obj.status == 'completed':
            # Once completed, prevent editing of progress and status
            return self.readonly_fields + ('progress', 'status')
        return self.readonly_fields