from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.db.models import Count, Q, Sum
from startups.models import Startup
from projects.models import Project
from tasks.models import Task
from investments.models import Investment
from funding.models import FundingApplication


# ==========================================================
# 🌐 UNIVERSAL DASHBOARD REDIRECT
# ==========================================================
@login_required
def dashboard_redirect(request):
    """Redirect users to their appropriate dashboard or fallback to home."""
    role = getattr(request.user, 'role', None)
    if role:
        role = role.lower()

    role_dashboards = {
        'manager': 'manager_dashboard',
        'founder': 'founder_dashboard',
        'team_member': 'team_dashboard',
        'investor': 'investor_dashboard',
    }

    target_url = role_dashboards.get(role, 'home')
    return redirect(target_url)


# ==========================================================
# 🧩 MANAGER DASHBOARD
# ==========================================================
@login_required
def manager_dashboard(request):
    """Venture Manager Dashboard"""
    role = getattr(request.user, 'role', '').lower()
    if role != 'manager':
        return redirect('dashboard_redirect')

    # Statistics
    total_startups = Startup.objects.count()
    total_projects = Project.objects.count()
    active_projects = Project.objects.filter(status='in_progress').count()
    completed_projects = Project.objects.filter(status='completed').count()

    # Task statistics
    total_tasks = Task.objects.count()
    completed_tasks = Task.objects.filter(status='completed').count()
    overdue_tasks = Task.objects.filter(
        due_date__lt=timezone.now().date()
    ).exclude(status='completed').count()

    # Recent activities
    recent_startups = Startup.objects.order_by('-created_at')[:5]
    recent_projects = Project.objects.select_related('startup').order_by('-created_at')[:5]

    context = {
        'total_startups': total_startups,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'recent_startups': recent_startups,
        'recent_projects': recent_projects,
    }
    return render(request, 'manager/dashboard.html', context)


@login_required
def founder_dashboard(request):
    """Founder Dashboard"""
    role = getattr(request.user, 'role', '').lower()
    if role != 'founder':
        return redirect('dashboard_redirect')

    user_startups = request.user.founded_startups.all()

    # Startup statistics
    total_startups = user_startups.count()
    active_startups = user_startups.filter(projects__status='in_progress').distinct().count()

    # Project statistics
    user_projects = Project.objects.filter(startup__in=user_startups)
    total_projects = user_projects.count()
    active_projects = user_projects.filter(status='in_progress').count()
    completed_projects = user_projects.filter(status='completed').count()

    # Task statistics
    user_tasks = Task.objects.filter(project__startup__in=user_startups)
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='completed').count()
    overdue_tasks = user_tasks.filter(
        due_date__lt=timezone.now().date()
    ).exclude(status='completed').count()

    # Funding statistics
    funding_applications = FundingApplication.objects.filter(startup__in=user_startups)
    pending_applications = funding_applications.filter(status__in=['submitted', 'under_review']).count()
    approved_applications = funding_applications.filter(status='approved').count()

    # Recent activities
    recent_projects = user_projects.select_related('startup').order_by('-created_at')[:5]
    recent_tasks = user_tasks.select_related('project', 'project__startup').order_by('-due_date')[:5]

    # Get first 3 startups for display
    featured_startups = user_startups[:3]

    context = {
        'user_startups': user_startups,
        'featured_startups': featured_startups,
        'total_startups': total_startups,
        'active_startups': active_startups,
        'total_projects': total_projects,
        'active_projects': active_projects,
        'completed_projects': completed_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'overdue_tasks': overdue_tasks,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'recent_projects': recent_projects,
        'recent_tasks': recent_tasks,
    }
    return render(request, 'founder/dashboard.html', context)

# ==========================================================
# 👥 TEAM MEMBER DASHBOARD
# ==========================================================
@login_required
def team_dashboard(request):
    """Team Member Dashboard"""
    role = getattr(request.user, 'role', '').lower()
    if role != 'team_member':
        return redirect('dashboard_redirect')

    # All tasks assigned to the current team member
    user_tasks = request.user.tasks.all()
    total_tasks = user_tasks.count()
    completed_tasks = user_tasks.filter(status='completed').count()
    has_tasks = user_tasks.exists()

    # Date calculations
    today = timezone.now().date()
    start_of_week = today - timezone.timedelta(days=today.weekday())
    end_of_week = start_of_week + timezone.timedelta(days=6)

    # Task insights
    due_this_week = user_tasks.filter(due_date__range=[start_of_week, end_of_week]).count()
    overdue_tasks = user_tasks.filter(due_date__lt=today).exclude(status='completed').count()
    completion_rate = (completed_tasks / total_tasks * 100) if total_tasks > 0 else 0

    # Projects linked to this user (via their tasks)
    active_projects = Project.objects.filter(
        tasks__assigned_to=request.user,
        status='in_progress'
    ).distinct().count()

    my_projects = Project.objects.filter(
        tasks__assigned_to=request.user
    ).select_related('startup').distinct()[:5]

    # Recent and urgent tasks
    recent_tasks = user_tasks.select_related('project', 'project__startup').order_by('-created_at')[:5]
    urgent_tasks = user_tasks.filter(
        priority='high',
        due_date__lte=today + timezone.timedelta(days=3)
    ).exclude(status='completed')[:5]

    context = {
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'due_this_week': due_this_week,
        'overdue_tasks': overdue_tasks,
        'active_projects': active_projects,
        'completion_rate': completion_rate,
        'recent_tasks': recent_tasks,
        'my_projects': my_projects,
        'urgent_tasks': urgent_tasks,
        'has_tasks': has_tasks,
    }

    return render(request, 'team/dashboard.html', context)

# ==========================================================
# 💰 INVESTOR DASHBOARD
# ==========================================================
from decimal import Decimal
from django.db.models import Sum
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect


def safe_sum_decimal(values):
    """Safely sum values as Decimal, handling floats and None."""
    total = Decimal(0)
    for v in values:
        try:
            total += Decimal(str(v or 0))
        except Exception:
            total += Decimal(0)
    return total


@login_required
def investor_dashboard(request):
    """Investor Dashboard"""
    role = getattr(request.user, 'role', '').lower()
    if role != 'investor':
        return redirect('dashboard_redirect')

    investments = request.user.investments.select_related('startup').all()
    total_investments = investments.count()
    active_investments = investments.filter(status='active').count()

    # 🧮 Ensure consistent Decimal math
    total_invested = safe_sum_decimal(inv.amount for inv in investments)
    portfolio_value = safe_sum_decimal(inv.current_value for inv in investments)
    total_return = portfolio_value - total_invested
    overall_roi = (total_return / total_invested * 100) if total_invested > 0 else Decimal(0)

    portfolio_growth = Decimal('12.5')  # Placeholder
    portfolio_startups = investments.values('startup').distinct().count()
    new_startups_this_quarter = investments.filter(
        investment_date__gte=timezone.now() - timezone.timedelta(days=90)
    ).values('startup').distinct().count()

    # ✅ FIX: use current_roi instead of roi
    avg_roi = (
        safe_sum_decimal(inv.current_roi for inv in investments) / total_investments
        if total_investments > 0 else Decimal(0)
    )

    recent_investments = investments.order_by('-investment_date')[:5]

    # Portfolio allocation by industry
    portfolio_allocation = investments.values('startup__industry').annotate(
        total_amount=Sum('amount')
    ).order_by('-total_amount')

    for allocation in portfolio_allocation:
        allocation['percentage'] = (
            (Decimal(allocation['total_amount'] or 0) / total_invested * 100)
            if total_invested > 0 else Decimal(0)
        )

    # Top performers — use current_roi
    top_performers = sorted(
        [inv for inv in investments if inv.current_roi > 0],
        key=lambda x: x.current_roi,
        reverse=True
    )[:3]

    recent_updates = []  # Placeholder for future updates

    context = {
        'total_invested': total_invested,
        'portfolio_value': portfolio_value,
        'total_return': total_return,
        'overall_roi': overall_roi,
        'portfolio_growth': portfolio_growth,
        'portfolio_startups': portfolio_startups,
        'new_startups_this_quarter': new_startups_this_quarter,
        'avg_roi': avg_roi,
        'active_investments': active_investments,
        'recent_investments': recent_investments,
        'portfolio_allocation': portfolio_allocation,
        'top_performers': top_performers,
        'recent_updates': recent_updates,
    }

    return render(request, 'investor/dashboard.html', context)
