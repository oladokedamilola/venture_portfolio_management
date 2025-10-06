# projects/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Q, Avg
from datetime import timedelta, time
from django.utils import timezone
from .models import Project
from tasks.models import Task
from .forms import ProjectForm
from tasks.forms import TaskCreateForm


@login_required
def project_list(request):
    if request.user.role.lower() == 'manager':
        projects = Project.objects.select_related('startup').annotate(
            task_count=Count('tasks'),
            completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
        ).order_by('-created_at')
        
        # Statistics for manager
        total_projects = projects.count()
        active_projects = projects.filter(status='in_progress').count()
        completed_projects = projects.filter(status='completed').count()
        
        return render(request, 'manager/projects.html', {
            'projects': projects,
            'total_projects': total_projects,
            'active_projects': active_projects,
            'completed_projects': completed_projects,
        })
    
    elif request.user.role.lower() == 'founder':
        projects = Project.objects.filter(startup__in=request.user.founded_startups.all())
        return render(request, 'founder/projects.html', {'projects': projects})
    
    elif request.user.role.lower() == 'team_member':
        projects = request.user.projects.all()
        return render(request, 'team/projects.html', {'projects': projects})
    
    else:
        projects = Project.objects.none()
        return render(request, 'projects.html', {'projects': projects})

@login_required
def project_detail(request, pk):
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if request.user.role.lower() == 'founder' and project.startup not in request.user.founded_startups.all():
        messages.error(request, 'You do not have permission to view this project.')
        return redirect('dashboard_redirect')
    
    template_map = {
        'manager': 'manager/project_detail.html',
        'founder': 'founder/project_detail.html',
        'team_member': 'team/project_detail.html',
    }
    template = template_map.get(request.user.role.lower(), 'project_detail.html')
    
    return render(request, template, {'project': project})


@login_required
def project_archive(request, pk):
    """Archive/unarchive a project using status field"""
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions (same as before)
    if request.user.role.lower() not in ['manager', 'founder']:
        messages.error(request, 'You do not have permission to archive projects.')
        return redirect('dashboard_redirect')
    
    if request.user.role.lower() == 'founder':
        if project.startup not in request.user.founded_startups.all():
            messages.error(request, 'You do not have permission to archive this project.')
            return redirect('dashboard_redirect')
    
    # Toggle between 'completed' and original status
    if project.status != 'completed':
        # Store original status and set to completed
        project._original_status = project.status
        project.status = 'completed'
        action = "archived"
    else:
        # Restore original status
        project.status = getattr(project, '_original_status', 'not_started')
        action = "unarchived"
    
    project.save()
    
    messages.success(request, f'Project "{project.name}" {action} successfully!')
    
    # Redirect based on user role
    if request.user.role.lower() == 'manager':
        return redirect('projects:manager_projects')
    else:
        return redirect('projects:founder_project_detail', pk=project.pk)

@login_required
def project_delete(request, pk):
    """Delete a project"""
    project = get_object_or_404(Project, pk=pk)
    
    # Check permissions
    if request.user.role.lower() == 'manager':
        # Managers can delete any project
        pass
    elif request.user.role.lower() == 'founder':
        # Founders can only delete projects from their startups
        if project.startup not in request.user.founded_startups.all():
            messages.error(request, 'You do not have permission to delete this project.')
            return redirect('dashboard_redirect')
    else:
        messages.error(request, 'You do not have permission to delete projects.')
        return redirect('dashboard_redirect')
    
    project_name = project.name
    project.delete()
    
    messages.success(request, f'Project "{project_name}" deleted successfully!')
    
    # Redirect based on user role
    if request.user.role.lower() == 'manager':
        return redirect('projects:manager_projects')
    else:
        return redirect('projects:founder_projects')

# projects/views.py
@login_required
def project_create_edit(request, pk=None):
    """
    Handle both project creation and editing in one view
    If pk is provided, we're editing. Otherwise, we're creating.
    """
    project = None
    editing = False
    
    # Check permissions
    if request.user.role.lower() not in ['manager', 'founder']:
        messages.error(request, 'You do not have permission to manage projects.')
        return redirect('dashboard_redirect')
    
    # If pk is provided, we're editing an existing project
    if pk:
        editing = True
        project = get_object_or_404(
            Project.objects.select_related('startup'),
            pk=pk
        )
        
        print(f"DEBUG: Editing project {project.name}")
        
        # Check edit permissions
        if request.user.role.lower() == 'founder':
            if project.startup not in request.user.founded_startups.all():
                messages.error(request, 'You do not have permission to edit this project.')
                return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project, user=request.user, editing=editing)
        if form.is_valid():
            project = form.save()
            
            action = "updated" if editing else "created"
            messages.success(request, f'Project "{project.name}" {action} successfully!')
            
            # Redirect based on user role
            if request.user.role.lower() == 'manager':
                return redirect('projects:manager_projects')
            else:
                return redirect('projects:founder_project_detail', pk=project.pk)
        else:
            print(f"DEBUG: Form errors: {form.errors}")
    else:
        form = ProjectForm(instance=project, user=request.user, editing=editing)
    
    # Determine template based on role and action
    template_map = {
        'manager': 'manager/project_form.html',
        'founder': 'founder/project_form.html',
    }
    template = template_map.get(request.user.role.lower(), 'project_form.html')
    
    return render(request, template, {
        'form': form,
        'project': project,
        'editing': editing
    })

# New manager-specific views
@login_required
def manager_projects(request):
    """Manager-specific projects view with enhanced analytics"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    projects = Project.objects.select_related('startup').annotate(
        task_count=Count('tasks'),
        completed_tasks=Count('tasks', filter=Q(tasks__status='completed'))
    ).order_by('-created_at')
    
    # Calculate all statistics
    total_projects = projects.count()
    active_projects = projects.filter(status='in_progress').count()
    completed_projects = projects.filter(status='completed').count()
    delayed_projects = projects.filter(status='delayed').count()
    on_hold_projects = projects.filter(status='on_hold').count()
    not_started_projects = projects.filter(status='not_started').count()
    
    # Priority counts
    high_priority_projects = projects.filter(priority='high').count()
    medium_priority_projects = projects.filter(priority='medium').count()
    low_priority_projects = projects.filter(priority='low').count()
    
    # Calculate active rate
    active_rate = (active_projects / total_projects * 100) if total_projects > 0 else 0
    
    # Get project choices directly from the model
    project_status_choices = Project.STATUS_CHOICES
    project_priority_choices = Project.PRIORITY_CHOICES
    
    return render(request, 'manager/projects.html', {
        'projects': projects,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'delayed_projects': delayed_projects,
        'on_hold_projects': on_hold_projects,
        'not_started_projects': not_started_projects,
        'high_priority_projects': high_priority_projects,
        'medium_priority_projects': medium_priority_projects,
        'low_priority_projects': low_priority_projects,
        'active_rate': active_rate,
        'project_status_choices': project_status_choices,
        'project_priority_choices': project_priority_choices,
    })
    
    
@login_required
def manager_project_detail(request, pk):
    """Manager-specific project detail view"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    project = get_object_or_404(
        Project.objects.select_related('startup')
                       .prefetch_related('tasks', 'tasks__assigned_to'),
        pk=pk
    )
    
    # Get project statistics
    tasks = project.tasks.all()
    completed_tasks = tasks.filter(status='completed').count()
    total_tasks = tasks.count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0
    
    # Overdue tasks
    overdue_tasks = tasks.filter(due_date__lt=timezone.now()).exclude(status='completed')
    
    # Handle task creation
    task_form = None
    if request.method == 'POST' and 'create_task' in request.POST:
        task_form = TaskCreateForm(request.POST, project=project)
        if task_form.is_valid():
            task = task_form.save(commit=False)
            task.project = project
            task.created_by = request.user
            task.save()
            messages.success(request, f'Task "{task.title}" created successfully!')
            return redirect('projects:manager_project_detail', pk=project.pk)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        task_form = TaskCreateForm(project=project)
    
    return render(request, 'manager/project_detail.html', {
        'project': project,
        'tasks': tasks,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'completion_rate': completion_rate,
        'overdue_tasks': overdue_tasks,
        'task_form': task_form,
    })

@login_required
def manager_project_analytics(request):
    """Manager project analytics dashboard"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    # Comprehensive project analytics
    projects = Project.objects.all()
    tasks = Task.objects.all()
    
    # Project completion trends
    completion_rates = []
    for status, label in Project.STATUS_CHOICES:
        count = projects.filter(status=status).count()
        completion_rates.append({
            'status': label,
            'count': count,
            'percentage': (count / projects.count() * 100) if projects.count() > 0 else 0
        })
    
    # Task completion analytics
    task_completion = tasks.values('status').annotate(
        count=Count('id'),
        percentage=Count('id') * 100.0 / tasks.count()
    )
    
    # Timeline performance
    on_time_projects = projects.filter(
        Q(end_date__isnull=True) | Q(end_date__gte=timezone.now())
    ).exclude(status='delayed').count()
    
    delayed_projects = projects.filter(status='delayed').count()
    
    # Team performance
    team_performance = Task.objects.values('assigned_to__username').annotate(
        total_tasks=Count('id'),
        completed_tasks=Count('id', filter=Q(status='completed')),
        completion_rate=Count('id', filter=Q(status='completed')) * 100.0 / Count('id')
    ).order_by('-completion_rate')
    
    return render(request, 'manager/project_analytics.html', {
        'completion_rates': completion_rates,
        'task_completion': task_completion,
        'on_time_projects': on_time_projects,
        'delayed_projects': delayed_projects,
        'team_performance': team_performance,
        'total_projects': projects.count(),
        'total_tasks': tasks.count(),
    })
    
    
