from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.urls import reverse
from .models import Startup, Project, Task, FundingRound
from .forms import StartupForm, ProjectForm, TaskForm, FundingForm


# --- Role Checks ---
def is_manager(user):
    return user.is_authenticated and user.role == "MANAGER"

def is_founder(user):
    return user.is_authenticated and user.role == "FOUNDER"

def is_investor(user):
    return user.is_authenticated and user.role == "INVESTOR"

def is_team_member(user):
    return user.is_authenticated and user.role == "TEAM"


# --- Startup Views ---
@login_required
def startup_list(request):
    user = request.user
    if user.role == "MANAGER":
        startups = Startup.objects.all()
    elif user.role == "FOUNDER":
        startups = Startup.objects.filter(projects__tasks__assigned_to=user).distinct()
    elif user.role == "INVESTOR":
        startups = Startup.objects.all()  # read-only in template
    elif user.role == "TEAM":
        startups = Startup.objects.filter(projects__tasks__assigned_to=user).distinct()
    else:
        startups = Startup.objects.none()
    return render(request, "portfolio/startup_list.html", {"startups": startups})


@login_required
def startup_detail(request, pk):
    startup = get_object_or_404(Startup, pk=pk)
    return render(request, "portfolio/startup_detail.html", {"startup": startup})


@user_passes_test(is_manager)
def startup_create(request):
    if request.method == "POST":
        form = StartupForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("startup_list")
    else:
        form = StartupForm()
    return render(request, "portfolio/startup_form.html", {"form": form})


@user_passes_test(is_manager)
def startup_edit(request, pk):
    startup = get_object_or_404(Startup, pk=pk)
    if request.method == "POST":
        form = StartupForm(request.POST, instance=startup)
        if form.is_valid():
            form.save()
            return redirect("startup_list")
    else:
        form = StartupForm(instance=startup)
    return render(request, "portfolio/startup_form.html", {"form": form})


@user_passes_test(is_manager)
def startup_delete(request, pk):
    startup = get_object_or_404(Startup, pk=pk)
    if request.method == "POST":
        startup.delete()
        return redirect("startup_list")
    return render(request, "portfolio/startup_confirm_delete.html", {"startup": startup})


# --- Project Views ---
@login_required
def project_create(request):
    if request.method == "POST":
        form = ProjectForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("startup_list")
    else:
        form = ProjectForm()
    return render(request, "portfolio/project_form.html", {"form": form})


# --- Task Views ---
@login_required
def task_create(request):
    if request.method == "POST":
        form = TaskForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("startup_list")
    else:
        form = TaskForm()
    return render(request, "portfolio/task_form.html", {"form": form})


# --- Funding Views ---
@login_required
def funding_create(request):
    if request.method == "POST":
        form = FundingForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("startup_list")
    else:
        form = FundingForm()
    return render(request, "portfolio/funding_form.html", {"form": form})
