# communications/urls.py
from django.urls import path
from . import views


urlpatterns = [
    path('notifications/', views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', views.mark_notification_read, name='mark_notification_read'),
    path('notifications/mark-all-read/', views.mark_all_notifications_read, name='mark_all_notifications_read'),
    path('api/notifications/count/', views.notification_count_api, name='notification_count_api'),
    path('api/notifications/recent/', views.recent_notifications_api, name='recent_notifications_api'),
    
    # Messages URLs
    path('messages/', views.messages_view, name='messages'),
    path('new-message/', views.new_message, name='new_message'),
    path('conversation/<int:conversation_id>/', views.messages_view, name='conversation_detail'),
    path('start-conversation/', views.start_conversation, name='start_conversation'),
    path('send-message/<int:conversation_id>/', views.send_message, name='send_message'),
    path('conversations/<int:conversation_id>/leave/', views.leave_conversation, name='leave_conversation'),
    path('start-direct-message/<int:user_id>/', views.start_direct_message, name='start_direct_message'),
]