# investments/forms.py
from django import forms
from .models import Investment

class InvestmentCreateForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ('startup', 'amount', 'equity', 'valuation', 'round', 'investment_date')
        widgets = {
            'investment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'equity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'valuation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'startup': forms.Select(attrs={'class': 'form-control'}),
            'round': forms.Select(attrs={'class': 'form-control'}),
        }
        labels = {
            'equity': 'Equity Percentage (%)',
            'valuation': 'Post-Money Valuation ($)',
        }
    
    def clean_equity(self):
        equity = self.cleaned_data.get('equity')
        if equity and (equity <= 0 or equity > 100):
            raise forms.ValidationError("Equity must be between 0.01% and 100%")
        return equity
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount <= 0:
            raise forms.ValidationError("Investment amount must be positive")
        return amount

class InvestmentEditForm(forms.ModelForm):
    class Meta:
        model = Investment
        fields = ('amount', 'equity', 'valuation', 'round', 'investment_date', 'status', 'current_valuation', 'exit_date', 'exit_value')
        widgets = {
            'investment_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'exit_date': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'amount': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'equity': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'max': '100'}),
            'valuation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'current_valuation': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'exit_value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'round': forms.Select(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        status = cleaned_data.get('status')
        exit_date = cleaned_data.get('exit_date')
        exit_value = cleaned_data.get('exit_value')
        
        if status == 'exited' and (not exit_date or not exit_value):
            raise forms.ValidationError("Exit date and value are required for exited investments")
        
        return cleaned_data