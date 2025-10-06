# investments/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Sum, Avg, Count, Q
from django.utils import timezone
from datetime import timedelta
from .models import Investment
from .forms import InvestmentCreateForm, InvestmentEditForm
from startups.models import Startup

@login_required
def investor_dashboard(request):
    """Enhanced Investor Dashboard"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    investments = request.user.investments.select_related('startup').all()
    
    # Core metrics
    total_invested = investments.aggregate(Sum('amount'))['amount__sum'] or 0
    portfolio_value = sum(float(inv.current_value) for inv in investments)
    portfolio_growth = ((portfolio_value - float(total_invested)) / float(total_invested) * 100) if total_invested > 0 else 0
    
    # Additional metrics
    active_investments = investments.filter(status='active')
    exited_investments = investments.filter(status='exited')
    
    # ROI calculations
    avg_roi = investments.aggregate(avg_roi=Avg('current_roi'))['avg_roi'] or 0
    
    # Stage distribution
    stage_distribution = investments.values('round').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    # Recent investments
    recent_investments = investments.order_by('-investment_date')[:5]
    
    # Portfolio allocation by industry
    portfolio_allocation = []
    industries = investments.values('startup__industry').annotate(
        total_amount=Sum('amount')
    )
    for industry in industries:
        if industry['startup__industry']:
            percentage = (industry['total_amount'] / total_invested * 100) if total_invested > 0 else 0
            portfolio_allocation.append({
                'industry': industry['startup__industry'],
                'amount': industry['total_amount'],
                'percentage': percentage,
                'color': f'hsl({hash(industry["startup__industry"]) % 360}, 70%, 50%)'
            })
    
    # Top performers
    top_performers = sorted(
        [inv for inv in investments if inv.current_roi > 0],
        key=lambda x: x.current_roi,
        reverse=True
    )[:3]
    
    context = {
        'investments': investments,
        'total_invested': total_invested,
        'portfolio_value': portfolio_value,
        'portfolio_growth': portfolio_growth,
        'portfolio_startups': investments.values('startup').distinct().count(),
        'active_investments': active_investments.count(),
        'exited_investments': exited_investments.count(),
        'avg_roi': avg_roi,
        'stage_distribution': stage_distribution,
        'recent_investments': recent_investments,
        'portfolio_allocation': portfolio_allocation,
        'top_performers': top_performers,
        'new_startups_this_quarter': investments.filter(
            investment_date__gte=timezone.now().date() - timedelta(days=90)
        ).count(),
    }
    
    return render(request, 'investor/dashboard.html', context)

# investments/views.py - Fix the investor_portfolio view
@login_required
def investor_portfolio(request):
    """Detailed Portfolio View"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    investments = request.user.investments.select_related('startup').all()
    
    # Filters
    status_filter = request.GET.get('status', 'all')
    round_filter = request.GET.get('round', 'all')
    
    if status_filter != 'all':
        investments = investments.filter(status=status_filter)
    if round_filter != 'all':
        investments = investments.filter(round=round_filter)
    
    # Portfolio statistics
    total_invested = investments.aggregate(Sum('amount'))['amount__sum'] or 0
    current_value = sum(float(inv.current_value) for inv in investments)
    
    # Stage breakdown
    stage_breakdown = investments.values('round').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    # Industry breakdown
    industry_breakdown = investments.values('startup__industry').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    # Fix the percentage calculation
    portfolio_growth = 0
    if total_invested > 0:
        portfolio_growth = ((current_value - float(total_invested)) / float(total_invested)) * 100
    
    context = {
        'investments': investments,
        'total_invested': total_invested,
        'current_value': current_value,
        'portfolio_growth': portfolio_growth,
        'stage_breakdown': stage_breakdown,
        'industry_breakdown': industry_breakdown,
        'status_filter': status_filter,
        'round_filter': round_filter,
        'total_startups': investments.values('startup').distinct().count(),
        'active_investments': investments.filter(status='active').count(),
    }
    
    return render(request, 'investor/portfolio.html', context)

@login_required
def funding_history(request):
    """Funding History Timeline"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    investments = request.user.investments.select_related('startup').order_by('-investment_date')
    
    # Group by year
    investments_by_year = {}
    for investment in investments:
        year = investment.investment_date.year
        if year not in investments_by_year:
            investments_by_year[year] = []
        investments_by_year[year].append(investment)
    
    # Yearly totals
    yearly_totals = investments.values('investment_date__year').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    ).order_by('-investment_date__year')
    
    context = {
        'investments': investments,
        'investments_by_year': investments_by_year,
        'yearly_totals': yearly_totals,
        'total_invested': investments.aggregate(total=Sum('amount'))['total'] or 0,
        'total_deals': investments.count(),
    }
    
    return render(request, 'investor/funding_history.html', context)

@login_required
def investment_create(request):
    """Create new investment"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = InvestmentCreateForm(request.POST)
        if form.is_valid():
            investment = form.save(commit=False)
            investment.investor = request.user
            investment.save()
            messages.success(request, f'Investment in {investment.startup.name} created successfully!')
            return redirect('investments:investor_portfolio')
    else:
        form = InvestmentCreateForm()
    
    return render(request, 'investor/investment_create.html', {'form': form})

@login_required
def investment_edit(request, pk):
    """Edit investment"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    investment = get_object_or_404(Investment, pk=pk, investor=request.user)
    
    if request.method == 'POST':
        form = InvestmentEditForm(request.POST, instance=investment)
        if form.is_valid():
            form.save()
            messages.success(request, f'Investment in {investment.startup.name} updated successfully!')
            return redirect('investments:investor_portfolio')
    else:
        form = InvestmentEditForm(instance=investment)
    
    return render(request, 'investor/investment_edit.html', {
        'form': form,
        'investment': investment
    })

@login_required
def investment_detail(request, pk):
    """Investment detail view"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    investment = get_object_or_404(Investment, pk=pk, investor=request.user)
    
    return render(request, 'investor/investment_detail.html', {
        'investment': investment
    })

@login_required
def investment_delete(request, pk):
    """Delete investment"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    investment = get_object_or_404(Investment, pk=pk, investor=request.user)
    
    if request.method == 'POST':
        startup_name = investment.startup.name
        investment.delete()
        messages.success(request, f'Investment in {startup_name} deleted successfully!')
        return redirect('investments:investor_portfolio')
    
    return render(request, 'investor/investment_delete.html', {
        'investment': investment
    })

@login_required
def portfolio_startups(request):
    """Portfolio startups view"""
    if request.user.role.lower() != 'investor':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    investments = request.user.investments.select_related('startup')
    startups = Startup.objects.filter(
        id__in=investments.values_list('startup', flat=True)
    ).distinct()
    
    # Add investment context
    startups_with_investment = []
    for startup in startups:
        startup_investments = investments.filter(startup=startup)
        total_invested = startup_investments.aggregate(total=Sum('amount'))['total'] or 0
        latest_investment = startup_investments.order_by('-investment_date').first()
        
        startups_with_investment.append({
            'startup': startup,
            'total_invested': total_invested,
            'latest_investment': latest_investment,
            'investment_count': startup_investments.count(),
            'current_roi': latest_investment.current_roi if latest_investment else 0,
        })
    
    # Sort by total invested
    startups_with_investment.sort(key=lambda x: x['total_invested'], reverse=True)
    
    context = {
        'startups_with_investment': startups_with_investment,
        'total_startups': len(startups_with_investment),
        'total_invested': sum(item['total_invested'] for item in startups_with_investment),
    }
    
    return render(request, 'investor/portfolio_startups.html', context)

# investments/views.py
@login_required
def investor_reports(request):
    # """Investor reports and analytics"""
    # if request.user.role.lower() != 'investor':
    #     messages.error(request, 'Access denied.')
    #     return redirect('dashboard_redirect')
    
    investments = request.user.investments.select_related('startup').all()
    
    # Performance metrics
    total_invested = investments.aggregate(total=Sum('amount'))['total'] or 0
    active_investments = investments.filter(status='active')
    
    # Calculate ROI manually since it's a property
    total_current_value = sum(float(inv.current_value) for inv in investments)
    total_roi = ((total_current_value - float(total_invested)) / float(total_invested) * 100) if total_invested > 0 else 0
    
    # Stage performance (without ROI aggregation)
    stage_performance = investments.values('round').annotate(
        total_invested=Sum('amount'),
        count=Count('id')
    )
    
    # Calculate average ROI per stage manually
    for stage in stage_performance:
        stage_investments = investments.filter(round=stage['round'])
        stage_roi_sum = sum(inv.current_roi for inv in stage_investments)
        stage['avg_roi'] = stage_roi_sum / len(stage_investments) if stage_investments else 0
    
    # Industry performance
    industry_performance = investments.values('startup__industry').annotate(
        total_invested=Sum('amount'),
        count=Count('id')
    )
    
    # Status distribution
    status_distribution = investments.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    # Recent investments for the report
    recent_investments = investments.order_by('-investment_date')[:10]
    
    # Performance by year
    investments_by_year = investments.values('investment_date__year').annotate(
        total_amount=Sum('amount'),
        count=Count('id')
    ).order_by('investment_date__year')
    
    context = {
        'total_invested': total_invested,
        'estimated_value': total_current_value,
        'total_roi': total_roi,
        'active_investments_count': active_investments.count(),
        'stage_performance': stage_performance,
        'industry_performance': industry_performance,
        'status_distribution': status_distribution,
        'total_startups': investments.values('startup').distinct().count(),
        'investments': investments,
        'recent_investments': recent_investments,
        'investments_by_year': investments_by_year,
    }
    
    return render(request, 'investor/reports.html', context)