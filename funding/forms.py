# funding/forms.py
from django import forms
from .models import FundingApplication

class FundingApplicationForm(forms.ModelForm):
    class Meta:
        model = FundingApplication
        fields = ('startup', 'funding_round', 'amount', 'equity_offered', 'valuation',
                 'pitch', 'use_of_funds', 'milestones', 'pitch_deck', 'financials')
        widgets = {
            'pitch': forms.Textarea(attrs={'rows': 6}),
            'use_of_funds': forms.Textarea(attrs={'rows': 4}),
            'milestones': forms.Textarea(attrs={'rows': 4}),
        }
    
    def __init__(self, *args, **kwargs):
        user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        if user:
            self.fields['startup'].queryset = user.founded_startups.all()