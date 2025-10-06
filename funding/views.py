# funding/views.py
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.db.models import Count, Q, Sum, Avg
from .models import FundingApplication
from .forms import FundingApplicationForm

@login_required
def funding_apply(request):
    if request.user.role.lower() != 'founder':
        messages.error(request, 'Only founders can apply for funding.')
        return redirect('dashboard_redirect')
    
    if request.method == 'POST':
        form = FundingApplicationForm(request.POST, request.FILES, user=request.user)
        if form.is_valid():
            application = form.save(commit=False)
            application.status = 'submitted'
            application.save()
            messages.success(request, 'Funding application submitted successfully!')
            return redirect('funding:founder_funding_rounds')
    else:
        form = FundingApplicationForm(user=request.user)
    
    return render(request, 'founder/funding_apply.html', {
        'form': form,
        'user_startups': request.user.founded_startups.all(),
    })

@login_required
def funding_rounds(request):
    """Generic funding rounds view that redirects based on user role"""
    if request.user.role.lower() == 'founder':
        applications = FundingApplication.objects.filter(startup__in=request.user.founded_startups.all())
        return render(request, 'founder/funding_rounds.html', {
            'applications': applications,
        })
    
    elif request.user.role.lower() == 'manager':
        return redirect('funding:manager_funding_rounds')
    
    else:
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')

# New manager-specific views
@login_required
def manager_funding_rounds(request):
    """Manager view for all funding applications with analytics"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    # Get all funding applications with related data
    applications = FundingApplication.objects.select_related('startup').prefetch_related(
        'startup__founders'
    ).order_by('-created_at')
    
    # Advanced statistics for manager - use the actual field names from your model
    total_applications = applications.count()
    pending_applications = applications.filter(status='submitted').count()
    approved_applications = applications.filter(status='approved').count()
    rejected_applications = applications.filter(status='rejected').count()
    
    # Funding amount statistics - use 'amount' field instead of 'amount_requested'
    funding_stats = applications.aggregate(
        total_amount=Sum('amount'),
        total_approved_amount=Sum('amount', filter=Q(status='approved'))
    )
    
    total_funding_amount = funding_stats['total_amount'] or 0
    total_approved_amount = funding_stats['total_approved_amount'] or 0
    
    # Applications by stage
    applications_by_stage = applications.values('startup__stage').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    # Applications by status
    applications_by_status = applications.values('status').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    )
    
    return render(request, 'manager/funding_rounds.html', {
        'applications': applications,
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'approved_applications': approved_applications,
        'rejected_applications': rejected_applications,
        'total_funding_amount': total_funding_amount,
        'total_approved_amount': total_approved_amount,
        'applications_by_stage': applications_by_stage,
        'applications_by_status': applications_by_status,
    })

@login_required
def manager_funding_detail(request, pk):
    """Manager view for detailed funding application review"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    application = get_object_or_404(
        FundingApplication.objects.select_related('startup').prefetch_related('startup__founders'),
        pk=pk
    )
    
    # Get related startup data
    startup = application.startup
    previous_applications = FundingApplication.objects.filter(
        startup=startup
    ).exclude(pk=pk).order_by('-created_at')
    
    # Get founders for display
    founders = startup.founders.all()
    
    return render(request, 'manager/funding_detail.html', {
        'application': application,
        'startup': startup,
        'founders': founders,
        'previous_applications': previous_applications,
    })

@login_required
def manager_funding_review(request, pk):
    """Manager view to review and update funding application status"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    application = get_object_or_404(FundingApplication, pk=pk)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        review_notes = request.POST.get('review_notes')
        
        if new_status in ['approved', 'rejected', 'under_review']:
            application.status = new_status
            if review_notes:
                # You might want to add a review_notes field to your model
                # For now, we'll store it in a different way or just use messages
                pass
            application.save()
            
            status_display = dict(FundingApplication.STATUS_CHOICES).get(new_status, new_status)
            messages.success(request, f'Application status updated to {status_display}.')
            return redirect('funding:manager_funding_detail', pk=application.pk)
        else:
            messages.error(request, 'Invalid status selected.')
    
    return render(request, 'manager/funding_review.html', {
        'application': application,
    })

@login_required
def funding_analytics(request):
    """Advanced analytics view for managers"""
    if request.user.role.lower() != 'manager':
        messages.error(request, 'Access denied.')
        return redirect('dashboard_redirect')
    
    # Comprehensive analytics data
    applications = FundingApplication.objects.select_related('startup').prefetch_related('startup__founders')
    
    # Monthly application trends
    from django.db.models.functions import TruncMonth
    monthly_trends = applications.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        count=Count('id'),
        total_amount=Sum('amount')
    ).order_by('month')
    
    # Success rate by startup stage
    success_by_stage = applications.values('startup__stage').annotate(
        total=Count('id'),
        approved=Count('id', filter=Q(status='approved')),
        success_rate=Count('id', filter=Q(status='approved')) * 100.0 / Count('id')
    )
    
    # Average funding amounts
    avg_amount = applications.aggregate(avg=Avg('amount'))['avg'] or 0
    avg_approved_amount = applications.filter(status='approved').aggregate(avg=Avg('amount'))['avg'] or 0
    
    return render(request, 'manager/funding_analytics.html', {
        'monthly_trends': monthly_trends,
        'success_by_stage': success_by_stage,
        'avg_amount': avg_amount,
        'avg_approved_amount': avg_approved_amount,
        'applications': applications,
    })