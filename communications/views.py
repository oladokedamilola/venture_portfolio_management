# communications/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib import messages
from .models import Notification, Message
from .services import NotificationService

from .models import Conversation, Message, ConversationMember, MessageRecipient
from .services import ConversationService
from .permissions import MessagePermissions
from django.contrib.auth import get_user_model

CustomUser = get_user_model()


@login_required
def notifications_view(request):
    """Display all notifications for the user"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    unread_count = NotificationService.get_unread_count(request.user)
    
    return render(request, 'communications/notifications.html', {
        'notifications': notifications,
        'unread_count': unread_count,
    })

@login_required
@require_http_methods(["POST"])
def mark_notification_read(request, pk):
    """Mark a specific notification as read"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.mark_as_read()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')

@login_required
@require_http_methods(["POST"])
def mark_all_notifications_read(request):
    """Mark all notifications as read for the user"""
    NotificationService.mark_all_as_read(request.user)
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notifications')

@login_required
def notification_count_api(request):
    """API endpoint to get unread notification count"""
    count = NotificationService.get_unread_count(request.user)
    return JsonResponse({'unread_count': count})

@login_required
def recent_notifications_api(request):
    """API endpoint to get recent notifications"""
    notifications = NotificationService.get_recent_notifications(request.user, limit=5)
    data = [
        {
            'id': n.id,
            'title': n.title,
            'message': n.message,
            'type': n.notification_type,
            'is_read': n.is_read,
            'action_url': n.action_url,
            'created_at': n.created_at.isoformat(),
            'time_ago': n.created_at.strftime('%b %d, %H:%M'),
        }
        for n in notifications
    ]
    return JsonResponse({'notifications': data})

@login_required
def messages_view(request, conversation_id=None):
    conversations = ConversationService.get_user_conversations(request.user)
    
    # Add last message and unread count to each conversation
    for conversation in conversations:
        conversation.last_message = conversation.messages.last()
        conversation.unread_count = Message.objects.filter(
            conversation=conversation
        ).exclude(
            sender=request.user
        ).filter(
            recipients__user=request.user,
            recipients__is_read=False
        ).count()
    
    active_conversation = None
    if conversation_id:
        active_conversation = get_object_or_404(Conversation, id=conversation_id)
        # Mark messages as read
        Message.objects.filter(
            conversation=active_conversation
        ).exclude(
            sender=request.user
        ).filter(
            recipients__user=request.user,
            recipients__is_read=False
        ).update(is_read=True)
    
    # Get available users for new messages (based on permissions)
    available_users = CustomUser.objects.exclude(id=request.user.id)
    available_users = [user for user in available_users 
                      if MessagePermissions.can_message_user(request.user, user)]
    
    return render(request, 'communications/messages.html', {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'available_users': available_users,
    })
    
    
@login_required
def conversation_list(request):
    """Get user's conversations"""
    conversations = ConversationService.get_user_conversations(request.user)
    # Return JSON or render template
    pass

@login_required
def messages_view(request, conversation_id=None):
    try:
        conversations = ConversationService.get_user_conversations(request.user)
        
        # Add last message and unread count to each conversation
        for conversation in conversations:
            # Get the last message
            conversation.last_message = conversation.messages.last()
            
            # Get unread count for this user in this conversation
            conversation.unread_count = Message.objects.filter(
                conversation=conversation
            ).exclude(
                sender=request.user
            ).filter(
                recipients__user=request.user,
                recipients__is_read=False
            ).count()
            
            # For direct conversations, get the other user
            if conversation.conversation_type == 'direct':
                conversation.other_user = ConversationService.get_other_user_in_direct_conversation(
                    conversation, request.user
                )
        
        active_conversation = None
        if conversation_id:
            # Verify user has access to this conversation
            if not ConversationMember.objects.filter(
                conversation_id=conversation_id, 
                user=request.user
            ).exists():
                return JsonResponse({'error': 'Access denied'}, status=403)
                
            active_conversation = get_object_or_404(Conversation, id=conversation_id)
            
            # Mark messages as read for this user in this conversation
            MessageRecipient.objects.filter(
                message__conversation=active_conversation,
                user=request.user,
                is_read=False
            ).update(is_read=True)
        
        # Get available users for new messages (based on permissions)
        available_users = CustomUser.objects.exclude(id=request.user.id)
        available_users = [user for user in available_users 
                          if MessagePermissions.can_message_user(request.user, user)]
        
        return render(request, 'communications/messages.html', {
            'conversations': conversations,
            'active_conversation': active_conversation,
            'available_users': available_users,
        })
        
    except Exception as e:
        # Log the error for debugging
        print(f"Error in messages_view: {str(e)}")
        return render(request, 'communications/messages.html', {
            'conversations': [],
            'active_conversation': None,
            'available_users': [],
            'error': str(e)
        })


# communications/views.py - Add this view
@login_required
def new_message(request):
    """New page for starting conversations"""
    available_users = CustomUser.objects.exclude(id=request.user.id)
    available_users = [user for user in available_users 
                      if MessagePermissions.can_message_user(request.user, user)]
    
    if request.method == 'POST':
        conversation_type = request.POST.get('conversation_type')
        recipient_id = request.POST.get('recipient_id')
        content = request.POST.get('content')
        
        if conversation_type == 'direct' and recipient_id:
            recipient = get_object_or_404(CustomUser, id=recipient_id)
            
            if not MessagePermissions.can_message_user(request.user, recipient):
                messages.error(request, 'Cannot message this user')
                return redirect('new_message')
            
            conversation, created = ConversationService.get_or_create_direct_conversation(
                request.user, recipient
            )
            
            # Send initial message
            if content:
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content,
                    message_type='text'
                )
                
                # Create recipient records
                for member in conversation.members.exclude(user=request.user):
                    MessageRecipient.objects.create(message=message, user=member.user)
            
            messages.success(request, 'Message sent successfully!')
            return redirect('conversation_detail', conversation_id=conversation.id)
        
        else:
            messages.error(request, 'Please select a recipient')
    
    return render(request, 'communications/new_message.html', {
        'available_users': available_users,
    })


@login_required
@require_http_methods(["POST"])
def start_conversation(request):
    """Start a new conversation"""
    try:
        conversation_type = request.POST.get('conversation_type')
        content = request.POST.get('content')
        
        if conversation_type == 'direct':
            recipient_id = request.POST.get('recipient_id')
            if not recipient_id:
                return JsonResponse({'error': 'Recipient is required'}, status=400)
            
            recipient = get_object_or_404(CustomUser, id=recipient_id)
            
            if not MessagePermissions.can_message_user(request.user, recipient):
                return JsonResponse({'error': 'Cannot message this user'}, status=403)
            
            conversation, created = ConversationService.get_or_create_direct_conversation(
                request.user, recipient
            )
            
            # Send initial message
            if content:
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content,
                    message_type='text'
                )
                
                # Create recipient records for all other members
                for member in ConversationMember.objects.filter(
                    conversation=conversation
                ).exclude(user=request.user):
                    MessageRecipient.objects.create(message=message, user=member.user)
            
            return redirect('conversation_detail', conversation_id=conversation.id)
            
        else:
            # Handle group conversations (startup, project, investment)
            return JsonResponse({'error': 'Group conversations not yet implemented'}, status=501)
            
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Check if user is member
        if not ConversationMember.objects.filter(
            conversation=conversation, 
            user=request.user
        ).exists():
            return JsonResponse({'error': 'Not a member of this conversation'}, status=403)
        
        content = request.POST.get('content')
        if not content:
            return JsonResponse({'error': 'Message content is required'}, status=400)
        
        message = Message.objects.create(
            conversation=conversation,
            sender=request.user,
            content=content,
            message_type='text'
        )
        
        # Handle file attachment
        if 'attachment' in request.FILES:
            message.attachment = request.FILES['attachment']
            message.attachment_name = request.FILES['attachment'].name
            message.save()
        
        # Create recipient records for unread tracking for all other members
        other_members = ConversationMember.objects.filter(
            conversation=conversation
        ).exclude(user=request.user)
        
        for member in other_members:
            MessageRecipient.objects.get_or_create(message=message, user=member.user)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message_id': message.id,
                'content': message.content,
                'created_at': message.created_at.isoformat(),
                'sender_name': message.sender.get_full_name() or message.sender.username
            })
        
        return redirect('conversation_detail', conversation_id=conversation.id)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
@require_http_methods(["POST"])
def leave_conversation(request, conversation_id):
    """Leave a conversation"""
    try:
        conversation = get_object_or_404(Conversation, id=conversation_id)
        
        # Remove user from conversation members
        ConversationMember.objects.filter(
            conversation=conversation,
            user=request.user
        ).delete()
        
        # If it's a direct message and no members left, archive the conversation
        if conversation.conversation_type == 'direct' and conversation.members.count() == 0:
            conversation.is_active = False
            conversation.save()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
        
        return redirect('messages')
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)

@login_required
def start_direct_message(request, user_id):
    """Start a direct message with another user (API endpoint)"""
    recipient = get_object_or_404(CustomUser, id=user_id)
    
    if not MessagePermissions.can_message_user(request.user, recipient):
        return JsonResponse({'error': 'Cannot message this user'}, status=403)
    
    conversation, created = ConversationService.get_or_create_direct_conversation(
        request.user, recipient
    )
    
    return JsonResponse({
        'conversation_id': conversation.id,
        'created': created,
        'redirect_url': f'/communications/conversation/{conversation.id}/'
    })