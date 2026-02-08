from django import forms
from .models import Referral, Offer

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