from django import forms
from .models import Startup


class StartupCreateForm(forms.ModelForm):
    class Meta:
        model = Startup
        fields = (
            'name', 'description', 'industry', 'stage', 'founding_date',
            'website', 'logo', 'location', 'team_size', 'market',
            'monthly_revenue', 'valuation'
        )
        # Exclude 'founder' since it’s auto-assigned
        widgets = {
            'description': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': 'Describe your startup’s mission, product, and value proposition...'
            }),
            'market': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Describe your target market, audience, and opportunity...'
            }),
            'founding_date': forms.DateInput(attrs={'type': 'date'}),
            'location': forms.TextInput(attrs={'placeholder': 'e.g., Lagos, Nigeria'}),
            'monthly_revenue': forms.NumberInput(attrs={'placeholder': '0.00'}),
            'valuation': forms.NumberInput(attrs={'placeholder': '0.00'}),
        }

        

class StartupEditForm(forms.ModelForm):
    class Meta:
        model = Startup
        fields = ('name', 'description', 'industry', 'stage', 'founding_date',
                 'website', 'logo', 'location', 'team_size', 'monthly_revenue', 'valuation', 'market')
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
            'market': forms.Textarea(attrs={'rows': 3}),
            'founding_date': forms.DateInput(attrs={'type': 'date'}),
        }