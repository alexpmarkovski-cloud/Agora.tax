from django import forms
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
from .models import Referral, Offer, CPAUser

class CPASignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    company_name = forms.CharField(max_length=255, label='Company Name')
    license_number = forms.CharField(max_length=50, label='CPA License Number')
    license_state = forms.CharField(max_length=2, label='License State (e.g., NY)')

    def save(self, request):
        # 1. Create the Django User
        user = super().save(request)
        
        # 2. Create the linked CPAUser
        # Note: Allauth handles saving the User model. We just add our extra data.
        CPAUser.objects.create(
            user=user,
            email=user.email, # Allauth ensures email is collected
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            company_name=self.cleaned_data['company_name'],
            license_number=self.cleaned_data['license_number'],
            license_state=self.cleaned_data['license_state']
        )
        return user

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