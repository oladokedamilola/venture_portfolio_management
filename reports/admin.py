# reports/admin.py
from django.contrib import admin
from django.utils.html import format_html
import json
from .models import Report

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'report_type_display',
        'generated_by',
        'file_link',
        'created_at',
        'content_preview'
    )
    list_filter = (
        'report_type',
        'created_at',
        'generated_by'
    )
    search_fields = (
        'name',
        'generated_by__username',
        'generated_by__email',
        'generated_by__first_name',
        'generated_by__last_name'
    )
    readonly_fields = (
        'created_at',
        'content_preview',
        'file_link_display'
    )
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Report Information', {
            'fields': (
                'name',
                'report_type',
                'generated_by'
            )
        }),
        ('Content', {
            'fields': (
                'content',
                'content_preview'
            )
        }),
        ('File Attachment', {
            'fields': (
                'file',
                'file_link_display'
            )
        }),
        ('Metadata', {
            'fields': (
                'created_at',
            ),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('generated_by')
    
    def report_type_display(self, obj):
        """Display formatted report type"""
        return obj.get_report_type_display()
    report_type_display.short_description = 'Report Type'
    
    def file_link(self, obj):
        """Display file as clickable link in list view"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank">📄 Download</a>',
                obj.file.url
            )
        return "No file"
    file_link.short_description = 'File'
    
    def file_link_display(self, obj):
        """Display file as clickable link in detail view"""
        if obj.file:
            return format_html(
                '<a href="{}" target="_blank" style="padding: 5px 10px; background: #007cba; color: white; text-decoration: none; border-radius: 3px;">📄 Download Report File</a>',
                obj.file.url
            )
        return "No file attached"
    file_link_display.short_description = 'Current File'
    file_link_display.allow_tags = True
    
    def content_preview(self, obj):
        """Display a preview of the JSON content"""
        if obj.content:
            try:
                # Format JSON for display, limit to 200 characters
                formatted_content = json.dumps(obj.content, indent=2)
                preview = formatted_content[:200] + "..." if len(formatted_content) > 200 else formatted_content
                return format_html('<pre style="background: #f5f5f5; padding: 10px; border-radius: 3px; overflow-x: auto; font-size: 12px;">{}</pre>', preview)
            except (TypeError, ValueError):
                return "Invalid JSON content"
        return "No content"
    content_preview.short_description = 'Content Preview'
    content_preview.allow_tags = True
    
    def download_report(self, request, queryset):
        """Admin action to download selected reports (placeholder for actual implementation)"""
        self.message_user(request, f'Download functionality would be implemented for {queryset.count()} report(s).')
    download_report.short_description = "Download selected reports"
    
    def generate_sample_data(self, request, queryset):
        """Admin action to generate sample JSON data for reports"""
        for report in queryset:
            if not report.content:
                sample_data = {
                    "report_metadata": {
                        "type": report.report_type,
                        "generated_at": report.created_at.isoformat(),
                        "pages": 15,
                        "data_points": 245
                    },
                    "summary": {
                        "total_startups": 12,
                        "total_investment": 4500000,
                        "average_roi": 0.23
                    },
                    "sections": ["executive_summary", "performance_metrics", "risk_analysis"]
                }
                report.content = sample_data
                report.save()
        self.message_user(request, f'Sample data generated for {queryset.count()} report(s).')
    generate_sample_data.short_description = "Generate sample data for selected reports"
    
    actions = [download_report, generate_sample_data]
    
    def save_model(self, request, obj, form, change):
        """Ensure generated_by is set to current user when creating new report"""
        if not obj.pk:  # Only for new objects
            obj.generated_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Make generated_by read-only after creation"""
        if obj:  # Editing an existing object
            return self.readonly_fields + ('generated_by',)
        return self.readonly_fields