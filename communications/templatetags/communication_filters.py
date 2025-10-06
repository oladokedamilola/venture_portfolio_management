# communications/templatetags/communication_filters.py
from django import template
from django.contrib.auth import get_user_model

register = template.Library()
CustomUser = get_user_model()

@register.filter
def exclude_user(queryset, user):
    """Exclude a specific user from a queryset"""
    if hasattr(queryset, 'exclude'):
        return queryset.exclude(id=user.id)
    elif hasattr(queryset, 'filter'):
        # Handle case where it might be a manager
        return queryset.filter(id__ne=user.id)
    return queryset

@register.filter
def get_other_user(conversation, current_user):
    """Get the other user in a direct conversation"""
    if conversation.conversation_type != 'direct':
        return None
    
    # Get the other member (excluding current user)
    other_members = conversation.members.exclude(id=current_user.id)
    return other_members.first() if other_members.exists() else None