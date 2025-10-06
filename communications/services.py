# communications/services.py
from django.utils import timezone
from django.db import transaction
from django.contrib.auth import get_user_model
from django.db.models import Q

from .models import Notification, Conversation, ConversationMember, Message, MessageRecipient
from startups.models import Startup
from investments.models import Investment

CustomUser = get_user_model()

class NotificationService:
    @staticmethod
    def create_notification(user, title, message, notification_type='info', action_url=None, 
                          related_object=None):
        """Create a new notification for a user"""
        notification = Notification.objects.create(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type,
            action_url=action_url,
            related_object_id=related_object.id if related_object else None,
            related_object_type=related_object.__class__.__name__ if related_object else None
        )
        return notification
    
    @staticmethod
    def create_bulk_notification(users, title, message, notification_type='info', action_url=None):
        """Create notifications for multiple users"""
        notifications = [
            Notification(
                user=user,
                title=title,
                message=message,
                notification_type=notification_type,
                action_url=action_url
            ) for user in users
        ]
        Notification.objects.bulk_create(notifications)
        return notifications
    
    @staticmethod
    def mark_all_as_read(user):
        """Mark all notifications as read for a user"""
        Notification.objects.filter(user=user, is_read=False).update(
            is_read=True, 
            read_at=timezone.now()
        )
    
    @staticmethod
    def get_unread_count(user):
        """Get count of unread notifications for a user"""
        return Notification.objects.filter(user=user, is_read=False).count()
    
    @staticmethod
    def get_recent_notifications(user, limit=10):
        """Get recent notifications for a user"""
        return Notification.objects.filter(user=user).order_by('-created_at')[:limit]


class ConversationService:
    
    @staticmethod
    def get_or_create_direct_conversation(user1, user2):
        """Get or create a direct message conversation between two users"""
        with transaction.atomic():
            # First, check if there's already a direct conversation between these users
            existing_conversations = Conversation.objects.filter(
                conversation_type='direct'
            ).filter(
                members__user=user1
            ).filter(
                members__user=user2
            ).distinct()
            
            if existing_conversations.exists():
                return existing_conversations.first(), False
            
            # Create new conversation
            title = f"Direct: {user1.get_full_name() or user1.username} & {user2.get_full_name() or user2.username}"
            
            conversation = Conversation.objects.create(
                conversation_type='direct',
                title=title,
                created_by=user1
            )
            
            # Add both users as members
            ConversationMember.objects.create(conversation=conversation, user=user1)
            ConversationMember.objects.create(conversation=conversation, user=user2)
            
            return conversation, True
    
    @staticmethod
    def create_startup_team_conversation(startup):
        """Create conversation for startup team members"""
        with transaction.atomic():
            conversation = Conversation.objects.create(
                title=f"Team: {startup.name}",
                conversation_type='startup',
                created_by=startup.founder,
                startup=startup
            )
            
            # Add founder
            ConversationMember.objects.create(
                conversation=conversation,
                user=startup.founder,
                is_admin=True
            )
            
            # Add team members
            # Note: Adjust this based on your actual team member relationship
            # This assumes startup.team_members is a ManyToMany field to CustomUser
            if hasattr(startup, 'team_members'):
                for member in startup.team_members.all():
                    ConversationMember.objects.create(
                        conversation=conversation,
                        user=member
                    )
            
            return conversation
    
    @staticmethod
    def create_investor_conversation(investment):
        """Create conversation between founders and investors for a specific investment"""
        with transaction.atomic():
            conversation = Conversation.objects.create(
                title=f"Investment: {investment.startup.name} - {investment.get_round_display()}",
                conversation_type='investment',
                created_by=investment.startup.founder,
                startup=investment.startup,
                investment=investment
            )
            
            # Add founder
            ConversationMember.objects.create(
                conversation=conversation,
                user=investment.startup.founder,
                is_admin=True
            )
            
            # Add investors
            # Note: Adjust this based on your actual investor relationship
            # This assumes investment.investors is a ManyToMany field to CustomUser
            if hasattr(investment, 'investors'):
                for investor in investment.investors.all():
                    ConversationMember.objects.create(
                        conversation=conversation,
                        user=investor
                    )
            
            return conversation
    
    @staticmethod
    def get_user_conversations(user):
        """Get all conversations a user is part of"""
        # Get conversation IDs where user is a member
        conversation_ids = ConversationMember.objects.filter(
            user=user
        ).values_list('conversation_id', flat=True)
        
        # Get conversations with prefetching
        conversations = Conversation.objects.filter(
            id__in=conversation_ids,
            is_active=True
        ).prefetch_related(
            'conversationmember_set__user',  # Prefetch members
            'messages',  # Prefetch messages
            'messages__sender',  # Prefetch message senders
            'startup',  # Prefetch startup if exists
            'investment'  # Prefetch investment if exists
        ).distinct().order_by('-messages__created_at')  # Order by latest message
        
        return conversations
    
    @staticmethod
    def get_conversation_members(conversation):
        """Get all members of a conversation"""
        return CustomUser.objects.filter(
            conversationmember__conversation=conversation
        ).select_related('avatar')
    
    @staticmethod
    def get_other_user_in_direct_conversation(conversation, current_user):
        """Get the other user in a direct conversation"""
        if conversation.conversation_type != 'direct':
            return None
        
        other_member = conversation.conversationmember_set.exclude(
            user=current_user
        ).select_related('user').first()
        
        return other_member.user if other_member else None
    
    @staticmethod
    def get_unread_message_count(conversation, user):
        """Get count of unread messages for a user in a conversation"""
        return Message.objects.filter(
            conversation=conversation
        ).exclude(
            sender=user
        ).filter(
            messagerecipient__user=user,
            messagerecipient__is_read=False
        ).count()
    
    @staticmethod
    def mark_conversation_as_read(conversation, user):
        """Mark all messages in a conversation as read for a user"""
        MessageRecipient.objects.filter(
            message__conversation=conversation,
            user=user,
            is_read=False
        ).update(is_read=True, read_at=timezone.now())
    
    @staticmethod
    def add_user_to_conversation(conversation, user, is_admin=False):
        """Add a user to a conversation"""
        member, created = ConversationMember.objects.get_or_create(
            conversation=conversation,
            user=user,
            defaults={'is_admin': is_admin}
        )
        return member, created
    
    @staticmethod
    def remove_user_from_conversation(conversation, user):
        """Remove a user from a conversation"""
        deleted_count, _ = ConversationMember.objects.filter(
            conversation=conversation,
            user=user
        ).delete()
        return deleted_count > 0
    
    @staticmethod
    def is_user_in_conversation(conversation, user):
        """Check if a user is a member of a conversation"""
        return ConversationMember.objects.filter(
            conversation=conversation,
            user=user
        ).exists()


class MessageService:
    
    @staticmethod
    def send_message(conversation, sender, content, message_type='text', attachment=None):
        """Send a message in a conversation"""
        with transaction.atomic():
            # Verify sender is in conversation
            if not ConversationService.is_user_in_conversation(conversation, sender):
                raise ValueError("Sender is not a member of this conversation")
            
            # Create message
            message = Message.objects.create(
                conversation=conversation,
                sender=sender,
                content=content,
                message_type=message_type,
                attachment=attachment
            )
            
            if attachment:
                message.attachment_name = attachment.name
                message.save()
            
            # Create recipient records for all other members
            other_members = ConversationMember.objects.filter(
                conversation=conversation
            ).exclude(user=sender)
            
            message_recipients = [
                MessageRecipient(message=message, user=member.user)
                for member in other_members
            ]
            
            if message_recipients:
                MessageRecipient.objects.bulk_create(message_recipients)
            
            return message
    
    @staticmethod
    def get_conversation_messages(conversation, limit=50):
        """Get messages from a conversation"""
        return Message.objects.filter(
            conversation=conversation
        ).select_related(
            'sender'
        ).prefetch_related(
            'recipients'
        ).order_by('-created_at')[:limit]
    
    @staticmethod
    def mark_message_as_read(message, user):
        """Mark a specific message as read for a user"""
        recipient, created = MessageRecipient.objects.get_or_create(
            message=message,
            user=user,
            defaults={'is_read': True, 'read_at': timezone.now()}
        )
        
        if not created and not recipient.is_read:
            recipient.is_read = True
            recipient.read_at = timezone.now()
            recipient.save()
        
        return recipient