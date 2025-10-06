# projects/forms.py
from django import forms
from .models import Project
from django.contrib.auth import get_user_model
from startups.models import Startup
from django.db.models import Q

CustomUser = get_user_model()

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        # REMOVED: 'team_members' from fields
        fields = ('name', 'description', 'startup', 'status', 'priority', 'progress',
                 'start_date', 'due_date', 'budget')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.editing = kwargs.pop('editing', False)
        super().__init__(*args, **kwargs)
        
        if self.user:
            print(f"DEBUG: User role: {self.user.role}")
            
            # Startup field logic
            if self.user.role == 'founder':
                self.fields['startup'].queryset = self.user.founded_startups.all()
                print(f"DEBUG: Founder startups: {self.fields['startup'].queryset.count()}")
            elif self.user.role == 'manager':
                self.fields['startup'].queryset = Startup.objects.all()
                print(f"DEBUG: Manager startups: {self.fields['startup'].queryset.count()}")
            
            # If editing, make startup field read-only
            if self.editing and self.instance.pk:
                self.fields['startup'].disabled = True
                self.fields['startup'].widget.attrs['title'] = 'Startup cannot be changed after creation'

    def save(self, commit=True):
        """Override save to set created_by for new projects"""
        instance = super().save(commit=False)
        
        # Set created_by for new projects
        if not self.instance.pk and self.user:
            instance.created_by = self.user
        
        if commit:
            instance.save()
        
        return instance