# communications/signals.py
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.utils import timezone

from startups.models import Startup
from projects.models import Project
from tasks.models import Task as TaskModel
from funding.models import FundingApplication
from investments.models import Investment

from .services import NotificationService

CustomUser = get_user_model()

# User signals
@receiver(post_save, sender=CustomUser)
def user_registration_notification(sender, instance, created, **kwargs):
    if created:
        NotificationService.create_notification(
            user=instance,
            title="Welcome to VentureNest!",
            message="Your account has been created successfully. Start exploring the platform.",
            notification_type='success',
            action_url='/dashboard/'
        )

# Startup signals
@receiver(post_save, sender=Startup)
def startup_created_notification(sender, instance, created, **kwargs):
    if created:
        # FIXED: Use founder (singular) instead of founders (plural)
        if instance.founder:
            NotificationService.create_notification(
                user=instance.founder,
                title="Startup Created",
                message=f"Your startup '{instance.name}' has been created successfully.",
                notification_type='success',
                action_url=f'/founder/startups/{instance.id}/'
            )
        
        # Notify managers about new startup
        managers = CustomUser.objects.filter(role='manager')
        for manager in managers:
            # FIXED: Use founder name instead of founders.first()
            founder_name = instance.founder.get_full_name() if instance.founder else "Unknown Founder"
            NotificationService.create_notification(
                user=manager,
                title="New Startup Created",
                message=f"New startup '{instance.name}' has been created by {founder_name}.",
                notification_type='info',
                action_url=f'/manager/startups/{instance.id}/'
            )

# Project signals - UPDATED: Removed team_members references
@receiver(post_save, sender=Project)
def project_created_notification(sender, instance, created, **kwargs):
    if created:
        # UPDATED: Notify the project creator instead of team members
        if instance.created_by:
            NotificationService.create_notification(
                user=instance.created_by,
                title="Project Created Successfully",
                message=f"Your project '{instance.name}' has been created successfully.",
                notification_type='success',
                action_url=f'/projects/{instance.id}/'
            )
        
        # UPDATED: Notify startup founder (if different from creator)
        if instance.startup and instance.startup.founder and instance.startup.founder != instance.created_by:
            NotificationService.create_notification(
                user=instance.startup.founder,
                title="New Project Created",
                message=f"A new project '{instance.name}' has been created for your startup '{instance.startup.name}'.",
                notification_type='info',
                action_url=f'/founder/projects/{instance.id}/'
            )

# UPDATED: Added project status change notification
@receiver(post_save, sender=Project)
def project_status_updated_notification(sender, instance, **kwargs):
    """Notify relevant users when project status changes"""
    if not kwargs.get('created', False):
        # Notify project creator
        if instance.created_by:
            NotificationService.create_notification(
                user=instance.created_by,
                title="Project Status Updated",
                message=f"Project '{instance.name}' status changed to {instance.get_status_display()}.",
                notification_type='info',
                action_url=f'/projects/{instance.id}/'
            )
        
        # Notify startup founder (if different from creator)
        if instance.startup and instance.startup.founder and instance.startup.founder != instance.created_by:
            NotificationService.create_notification(
                user=instance.startup.founder,
                title="Project Status Updated",
                message=f"Project '{instance.name}' status changed to {instance.get_status_display()}.",
                notification_type='info',
                action_url=f'/founder/projects/{instance.id}/'
            )

# Task signals
@receiver(post_save, sender=TaskModel)
def task_assigned_notification(sender, instance, created, **kwargs):
    if created and instance.assigned_to:
        NotificationService.create_notification(
            user=instance.assigned_to,
            title="New Task Assigned",
            message=f"New task '{instance.title}' has been assigned to you.",
            notification_type='info',
            action_url=f'/tasks/{instance.id}/'
        )

@receiver(post_save, sender=TaskModel)
def task_status_updated_notification(sender, instance, **kwargs):
    if not kwargs.get('created', False):
        # FIXED: Use startup founder instead of founders.first()
        project_manager = instance.project.startup.founder if instance.project and instance.project.startup else None
        if project_manager and project_manager != instance.assigned_to:
            NotificationService.create_notification(
                user=project_manager,
                title="Task Status Updated",
                message=f"Task '{instance.title}' status changed to {instance.get_status_display()}.",
                notification_type='info',
                action_url=f'/tasks/{instance.id}/'
            )

# Funding signals
@receiver(post_save, sender=FundingApplication)
def funding_application_submitted(sender, instance, created, **kwargs):
    if created:
        # FIXED: Use founder (singular) instead of founders (plural)
        if instance.startup and instance.startup.founder:
            NotificationService.create_notification(
                user=instance.startup.founder,
                title="Funding Application Submitted",
                message=f"Your funding application for {instance.get_funding_round_display()} round has been submitted.",
                notification_type='success',
                action_url=f'/founder/funding/rounds/'
            )
        
        # Notify managers
        managers = CustomUser.objects.filter(role='manager')
        for manager in managers:
            NotificationService.create_notification(
                user=manager,
                title="New Funding Application",
                message=f"New funding application from {instance.startup.name if instance.startup else 'Unknown Startup'} for {instance.get_funding_round_display()} round.",
                notification_type='info',
                action_url=f'/manager/funding/applications/'
            )

@receiver(post_save, sender=FundingApplication)
def funding_application_status_change(sender, instance, **kwargs):
    if not kwargs.get('created', False):
        # FIXED: Use founder (singular) instead of founders (plural)
        if instance.startup and instance.startup.founder:
            NotificationService.create_notification(
                user=instance.startup.founder,
                title="Funding Application Update",
                message=f"Your funding application status changed to {instance.get_status_display()}.",
                notification_type='info' if instance.status == 'under_review' else 'success' if instance.status == 'approved' else 'error',
                action_url=f'/founder/funding/rounds/'
            )

# Additional safety signals with null checks
@receiver(post_save, sender=Startup)
def startup_updated_notification(sender, instance, created, **kwargs):
    """Notify founder when startup details are updated"""
    if not created and instance.founder:
        NotificationService.create_notification(
            user=instance.founder,
            title="Startup Updated",
            message=f"Your startup '{instance.name}' details have been updated.",
            notification_type='info',
            action_url=f'/founder/startups/{instance.id}/'
        )

@receiver(post_save, sender=Investment)
def investment_created_notification(sender, instance, created, **kwargs):
    """Notify when a new investment is made"""
    if created:
        # Notify startup founder
        if instance.startup and instance.startup.founder:
            NotificationService.create_notification(
                user=instance.startup.founder,
                title="New Investment",
                message=f"New investment of ${instance.amount} has been made in your startup.",
                notification_type='success',
                action_url=f'/founder/investments/'
            )
        
        # Notify investor if they are a user in the system
        if instance.investor and hasattr(instance.investor, 'user'):
            NotificationService.create_notification(
                user=instance.investor.user,
                title="Investment Recorded",
                message=f"Your investment of ${instance.amount} in {instance.startup.name} has been recorded.",
                notification_type='success',
                action_url=f'/investor/portfolio/'
            )

# UPDATED: Project deletion notification
@receiver(post_delete, sender=Project)
def project_deleted_notification(sender, instance, **kwargs):
    """Notify when a project is deleted"""
    if instance.created_by:
        NotificationService.create_notification(
            user=instance.created_by,
            title="Project Deleted",
            message=f"Project '{instance.name}' has been deleted.",
            notification_type='warning',
            action_url='/projects/'
        )
    
    # Also notify startup founder if different from creator
    if instance.startup and instance.startup.founder and instance.startup.founder != instance.created_by:
        NotificationService.create_notification(
            user=instance.startup.founder,
            title="Project Deleted",
            message=f"Project '{instance.name}' has been deleted from your startup.",
            notification_type='warning',
            action_url='/founder/projects/'
        )