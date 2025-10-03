from django import forms
from .models import Startup, Project, Task, FundingRound

class StartupForm(forms.ModelForm):
    class Meta:
        model = Startup
        fields = ["name", "description", "stage"]

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ["startup", "title", "description", "deadline"]

class TaskForm(forms.ModelForm):
    class Meta:
        model = Task
        fields = ["project", "title", "description", "status", "deadline", "assigned_to"]

class FundingForm(forms.ModelForm):
    class Meta:
        model = FundingRound
        fields = ["startup", "round_type", "amount", "date"]
