# communications/permissions.py
from django.contrib.auth import get_user_model
from investments.models import Investment


CustomUser = get_user_model()

class MessagePermissions:
    
    @staticmethod
    def can_message_user(sender, recipient):
        """Check if a user can message another user"""
        # Users can't message themselves
        if sender == recipient:
            return False
        
        # Based on roles and relationships
        if sender.role == 'investor' and recipient.role == 'founder':
            # Investors can message founders they've invested in
            return Investment.objects.filter(
                startup__founder=recipient,
                investors=sender
            ).exists()
        
        elif sender.role == 'founder' and recipient.role == 'investor':
            # Founders can message their investors
            return Investment.objects.filter(
                startup__founder=sender,
                investors=recipient
            ).exists()
        
        elif sender.role == 'founder' and recipient.role == 'team_member':
            # Founders can message their team members
            return recipient.teams.filter(startup__founder=sender).exists()
        
        elif sender.role == 'team_member' and recipient.role == 'founder':
            # Team members can message their founder
            return sender.teams.filter(startup__founder=recipient).exists()
        
        elif sender.role == 'team_member' and recipient.role == 'team_member':
            # Team members can message colleagues in same startup
            sender_startups = set(sender.teams.values_list('startup_id', flat=True))
            recipient_startups = set(recipient.teams.values_list('startup_id', flat=True))
            return bool(sender_startups.intersection(recipient_startups))
        
        # Venture managers have broader messaging privileges
        elif sender.role == 'manager':
            return True
        
        # Default deny
        return False