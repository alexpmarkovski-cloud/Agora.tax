from django import forms
from django.contrib.auth.models import User
from .models import Referral, Offer

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class ReferralForm(forms.ModelForm):
    class Meta:
        model = Referral
        fields = ['offer', 'client_email']
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-select'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control'}),
        }

    # This ensures users can't pick "Dead" offers
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['offer'].queryset = Offer.objects.filter(is_active=True)
        self.fields['offer'].label_from_instance = self.label_from_instance

    @staticmethod
    def label_from_instance(obj):
        return f"{obj.name} - Client Gets: {obj.client_bonus_summary}"