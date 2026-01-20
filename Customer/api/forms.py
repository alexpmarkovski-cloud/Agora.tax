from django import forms
from .models import Referral, Offer

class ReferralForm(forms.ModelForm):
    class Meta:
        model = Referral
        # REMOVE 'cpa' from this list!
        fields = ['offer', 'client_email']

    # This ensures users can't pick "Dead" offers
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['offer'].queryset = Offer.objects.filter(is_active=True)