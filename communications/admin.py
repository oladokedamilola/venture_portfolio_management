# communications/admin.py
from django.contrib import admin
from .models import Notification, Message, Conversation, ConversationMember, MessageRecipient

class ConversationMemberInline(admin.TabularInline):
    model = ConversationMember
    extra = 1
    autocomplete_fields = ['user']

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__email', 'title', 'message')
    readonly_fields = ('created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        (None, {
            'fields': ('user', 'title', 'message')
        }),
        ('Notification Settings', {
            'fields': ('notification_type', 'is_read')
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('title', 'conversation_type', 'created_by', 'created_at', 'is_active')
    list_filter = ('conversation_type', 'is_active', 'created_at')
    search_fields = ('title', 'created_by__username', 'created_by__email')
    readonly_fields = ('created_at',)
    list_per_page = 20
    inlines = [ConversationMemberInline]
    
    fieldsets = (
        (None, {
            'fields': ('title', 'conversation_type', 'created_by')
        }),
        ('Context', {
            'fields': ('startup', 'project', 'investment'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        })
    )

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'sender', 'message_type', 'created_at', 'is_edited')
    list_filter = ('message_type', 'is_edited', 'created_at')
    search_fields = (
        'sender__username', 
        'sender__email',
        'content',
        'conversation__title'
    )
    readonly_fields = ('created_at', 'updated_at')
    date_hierarchy = 'created_at'
    list_per_page = 20
    
    fieldsets = (
        ('Conversation', {
            'fields': ('conversation', 'sender')
        }),
        ('Message Content', {
            'fields': ('content', 'message_type')
        }),
        ('Attachments', {
            'fields': ('attachment', 'attachment_name'),
            'classes': ('collapse',)
        }),
        ('Related Objects', {
            'fields': ('related_object_id', 'related_object_type'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'is_edited'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('sender', 'conversation')

@admin.register(ConversationMember)
class ConversationMemberAdmin(admin.ModelAdmin):
    list_display = ('conversation', 'user', 'joined_at', 'is_admin')
    list_filter = ('is_admin', 'joined_at')
    search_fields = ('conversation__title', 'user__username', 'user__email')
    readonly_fields = ('joined_at',)
    list_per_page = 20
    autocomplete_fields = ['conversation', 'user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('conversation', 'user')

@admin.register(MessageRecipient)
class MessageRecipientAdmin(admin.ModelAdmin):
    list_display = ('message', 'user', 'is_read', 'read_at')
    list_filter = ('is_read', 'read_at')
    search_fields = ('message__content', 'user__username', 'user__email')
    readonly_fields = ('read_at',)
    list_per_page = 20
    autocomplete_fields = ['message', 'user']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('message', 'user')
    
    def mark_as_read(self, request, queryset):
        """Admin action to mark selected message recipients as read"""
        from django.utils import timezone
        updated = queryset.update(is_read=True, read_at=timezone.now())
        self.message_user(request, f'{updated} message(s) marked as read.')
    mark_as_read.short_description = "Mark selected messages as read"
    
    def mark_as_unread(self, request, queryset):
        """Admin action to mark selected message recipients as unread"""
        updated = queryset.update(is_read=False, read_at=None)
        self.message_user(request, f'{updated} message(s) marked as unread.')
    mark_as_unread.short_description = "Mark selected messages as unread"
    
    actions = [mark_as_read, mark_as_unread]