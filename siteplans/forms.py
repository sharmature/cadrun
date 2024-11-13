from django import forms
from .models import SitePlan

class SitePlanForm(forms.ModelForm):
    class Meta:
        model = SitePlan
        fields = ['site_name', 'address', 'city']
        widgets = {
            'site_name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter site name',
                'required': 'required'
            }),
            'address': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Enter address',
                'required': 'required'
            }),
        }
