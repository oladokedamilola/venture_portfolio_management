# tasks/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.utils import timezone
from .models import Task
from .forms import TaskUpdateForm, TaskEditForm

@login_required
def task_list(request):
    if request.user.role.lower() == 'manager':
        tasks = Task.objects.all()
    elif request.user.role.lower() == 'founder':
        tasks = Task.objects.filter(project__startup__in=request.user.founded_startups.all())
    elif request.user.role.lower() == 'team_member':
        tasks = request.user.tasks.all()
    else:
        tasks = Task.objects.none()
    
    template_map = {
        'manager': 'manager/tasks.html',
        'founder': 'founder/tasks.html',
        'team_member': 'team/tasks.html',
    }
    template = template_map.get(request.user.role.lower(), 'tasks.html')
    
    return render(request, template, {'tasks': tasks})

@login_required
def task_detail(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Check permissions
    if request.user.role.lower() == 'team_member' and task.assigned_to != request.user:
        messages.error(request, 'You do not have permission to view this task.')
        return redirect('team_dashboard')
    
    template_map = {
        'manager': 'manager/task_detail.html',
        'founder': 'founder/task_detail.html',
        'team_member': 'team/task_detail.html',
    }
    template = template_map.get(request.user.role.lower(), 'task_detail.html')
    
    return render(request, template, {'task': task})

@login_required
def task_update(request, pk):
    task = get_object_or_404(Task, pk=pk)
    
    # Check permissions
    if request.user.role.lower() == 'team_member' and task.assigned_to != request.user:
        messages.error(request, 'You can only update tasks assigned to you.')
        return redirect('team_dashboard')
    
    if request.method == 'POST':
        form = TaskUpdateForm(request.POST, instance=task)
        if form.is_valid():
            task = form.save(commit=False)
            task.updated_at = timezone.now()
            task.save()
            messages.success(request, 'Task updated successfully!')
            return redirect('team_task_detail', pk=task.pk)
    else:
        form = TaskUpdateForm(instance=task)
    
    return render(request, 'team/task_update.html', {'form': form, 'task': task})