from django.shortcuts import redirect
from django.contrib.auth.decorators import login_required

@login_required
def redirect_dashboard(request):
    user = request.user

    if user.role == "MANAGER":
        return redirect("manager_dashboard")
    elif user.role == "FOUNDER":
        return redirect("founder_dashboard")
    elif user.role == "TEAM":
        return redirect("team_dashboard")
    elif user.role == "INVESTOR":
        return redirect("investor_dashboard")
    elif user.role == "STAFF":
        return redirect("staff_dashboard")
    else:
        return redirect("default_dashboard")
