from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count
from .models import Startup
from .forms import StartupCreateForm, StartupEditForm
from django.core.paginator import Paginator

# ==============================
# 🔹 Manager-Specific Views
# ==============================

@login_required
def manager_startup_list(request):
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    startups = Startup.objects.all().annotate(
        project_count=Count('projects', distinct=True),
        task_count=Count('projects__tasks', distinct=True)
    ).order_by('-created_at')
    
    stage_counts = {
        'idea': startups.filter(stage='idea').count(),
        'pre_seed': startups.filter(stage='pre_seed').count(),
        'seed': startups.filter(stage='seed').count(),
        'series_a': startups.filter(stage='series_a').count(),
        'series_b': startups.filter(stage='series_b').count(),
        'growth': startups.filter(stage='growth').count(),
    }
    
    return render(request, 'manager/startup_list.html', {
        'startups': startups,
        'total_startups': startups.count(),
        'stage_counts': stage_counts,
    })


@login_required
def manager_startup_detail(request, pk):
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    startup = get_object_or_404(Startup, pk=pk)
    projects = startup.projects.all()
    investments = startup.investments.all() if hasattr(startup, 'investments') else []
    
    return render(request, 'manager/startup_detail.html', {
        'startup': startup,
        'projects': projects,
        'investments': investments,
    })


@login_required
def manager_startup_create(request):
    """Manager-specific startup creation view"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Only managers can access this page.')
        return redirect('dashboard_redirect')
    
    print(f"=== MANAGER STARTUP CREATE ===")
    print(f"User: {request.user} (Role: {request.user.role})")
    print(f"Method: {request.method}")
    
    if request.method == 'POST':
        print("POST request received")
        form = StartupCreateForm(request.POST, request.FILES)
        
        if form.is_valid():
            print("✅ Form is valid - saving startup")
            startup = form.save(commit=False)
            startup.founder = request.user   # 🔹 Assign manager as founder automatically
            startup.save()
            print(f"✅ Startup saved: {startup.name} (ID: {startup.id})")
            
            messages.success(request, f'Startup "{startup.name}" created successfully!')
            return redirect('startups:manager_startup_list')
        else:
            print("❌ Form is NOT valid")
            print(f"Form errors: {form.errors}")
    else:
        print("GET request - showing empty form")
        form = StartupCreateForm()
    
    return render(request, 'manager/startup_create.html', {'form': form})


@login_required
def manager_startup_dashboard(request):
    """Manager dashboard with startup statistics"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    startups = Startup.objects.all()
    total_startups = startups.count()
    active_startups = startups.filter(is_active=True).count()
    
    startups_by_stage = startups.values('stage').annotate(count=Count('id'))
    stage_data = {item['stage']: item['count'] for item in startups_by_stage}
    
    return render(request, 'manager/dashboard.html', {
        'total_startups': total_startups,
        'active_startups': active_startups,
        'stage_data': stage_data,
    })


# ==============================
# 🔹 Founder-Specific Views
# ==============================

@login_required
def founder_startup_list(request):
    if request.user.role.lower() != 'founder':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')

    # 🔹 Optional stage filtering
    stage_filter = request.GET.get('stage', 'all')

    startups = Startup.objects.filter(founder=request.user).annotate(
        project_count=Count('projects', distinct=True)
    ).order_by('-created_at')

    if stage_filter != 'all':
        startups = startups.filter(stage=stage_filter)

    total_startups = startups.count()

    # 🔹 Stage counts (for cards & pie section)
    stage_counts = {
        stage: Startup.objects.filter(founder=request.user, stage=stage).count()
        for stage, _ in Startup.STAGE_CHOICES
    }

    # 🔹 Add fallback demo values (so dashboard feels alive if empty)
    if total_startups == 0:
        stage_counts = {
            "idea": 1,
            "pre_seed": 2,
            "seed": 1,
            "series_a": 0,
            "series_b": 0,
            "growth": 0,
        }

    # 🔹 Pagination (6 startups per page)
    paginator = Paginator(startups, 6)
    page_number = request.GET.get('page')
    startups_page = paginator.get_page(page_number)

    context = {
        "startups": startups_page,
        "total_startups": total_startups,
        "stage_counts": stage_counts,
    }

    return render(request, "founder/startup_list.html", context)



@login_required
def founder_startup_detail(request, pk):
    if request.user.role.lower() != 'founder':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    startup = get_object_or_404(Startup, pk=pk, founder=request.user)
    projects = startup.projects.all()
    
    return render(request, 'founder/startup_detail.html', {
        'startup': startup,
        'projects': projects,
    })


@login_required
def founder_startup_create(request):
    """Founder-specific startup creation view"""
    if request.user.role.lower() != 'founder':
        messages.error(request, 'Only founders can access this page.')
        return redirect('dashboard_redirect')
    
    print(f"=== FOUNDER STARTUP CREATE ===")
    print(f"User: {request.user} (Role: {request.user.role})")
    
    if request.method == 'POST':
        form = StartupCreateForm(request.POST, request.FILES)
        if form.is_valid():
            startup = form.save(commit=False)
            startup.founder = request.user  # 🔹 Automatically assign founder
            startup.save()
            messages.success(request, 'Startup created successfully!')
            return redirect('startups:founder_startup_detail', pk=startup.pk)
        else:
            print("❌ Form is NOT valid")
            print(f"Form errors: {form.errors}")
    else:
        form = StartupCreateForm()
    
    return render(request, 'founder/startup_create.html', {'form': form})


# ==============================
# 🔹 Shared CRUD Views
# ==============================

@login_required
def startup_edit(request, pk):
    startup = get_object_or_404(Startup, pk=pk)
    
    if request.user.role.lower() not in ['manager', 'founder']:
        messages.error(request, 'You do not have permission to edit this startup.')
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = StartupEditForm(request.POST, request.FILES, instance=startup)
        if form.is_valid():
            form.save()
            messages.success(request, 'Startup updated successfully!')
            if request.user.role.lower() == 'founder':
                return redirect('startups:founder_startup_detail', pk=startup.pk)
            else:
                return redirect('startups:manager_startup_detail', pk=startup.pk)
    else:
        form = StartupEditForm(instance=startup)
    
    template = (
        'founder/startup_edit.html'
        if request.user.role.lower() == 'founder'
        else 'manager/startup_edit.html'
    )
    return render(request, template, {'form': form, 'startup': startup})


@login_required
def startup_delete(request, pk):
    startup = get_object_or_404(Startup, pk=pk)
    
    if request.user.role.lower() not in ['manager', 'founder']:
        messages.error(request, 'You do not have permission to delete this startup.')
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        startup_name = startup.name
        startup.delete()
        messages.success(request, f'Startup "{startup_name}" has been deleted successfully.')
        
        if request.user.role.lower() == 'founder':
            return redirect('startups:founder_startup_list')
        else:
            return redirect('startups:manager_startup_list')
    
    template = (
        'founder/startup_confirm_delete.html'
        if request.user.role.lower() == 'founder'
        else 'manager/startup_confirm_delete.html'
    )
    return render(request, template, {'startup': startup})
