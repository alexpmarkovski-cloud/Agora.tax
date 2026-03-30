from django import forms
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
import threading
from .models import Referral, Offer, CPAUser, CPALicense
from .services.nasba_scraper import verify_cpa_nasba

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
        cpa = CPAUser.objects.create(
            user=user,
            email=user.email, # Allauth ensures email is collected
            first_name=self.cleaned_data['first_name'],
            last_name=self.cleaned_data['last_name'],
            company_name=self.cleaned_data['company_name']
        )
        
        # 3. Create the initial CPALicense
        license = CPALicense.objects.create(
            cpa=cpa,
            state=self.cleaned_data['license_state'],
            license_number=self.cleaned_data['license_number']
        )
        
        # 4. Fire background thread for automatic NASBA verification
        def bg_verify(lic_pk):
            try:
                # Need to re-fetch inside thread to ensure state is fresh
                lic = CPALicense.objects.get(pk=lic_pk)
                result = verify_cpa_nasba(
                    first_name=lic.cpa.first_name,
                    last_name=lic.cpa.last_name,
                    state=lic.state,
                    license_number=lic.license_number
                )
                if result.get('is_valid'):
                    lic.is_verified = True
                    lic.save()
            except Exception as e:
                print(f"Background verification failed: {e}")
                
        threading.Thread(target=bg_verify, args=(license.pk,), daemon=True).start()
        
        return user

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'class': 'form-control'}),
        }

class CPALicenseForm(forms.ModelForm):
    class Meta:
        model = CPALicense
        fields = ['state', 'license_number']
        widgets = {
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., NY'}),
            'license_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'License Number'}),
        }

class ReferralForm(forms.ModelForm):
    client_type = forms.ChoiceField(
        choices=[('', 'Select Client Type'), ('Individual', 'Individual'), ('Business', 'Business')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ChoiceField(
        choices=[('', 'Select Category')],
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    class Meta:
        model = Referral
        fields = ['client_type', 'category', 'offer', 'client_email']
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

class ContactInquiryForm(forms.Form):
    INQUIRY_CHOICES = [
        ('', 'Select Inquiry Type'),
        ('General Support', 'General Support'),
        ('Payout Issue', 'Payout Issue'),
        ('Offer Inquiry', 'Offer Inquiry'),
        ('Technical Issue', 'Technical Issue'),
        ('Other', 'Other')
    ]
    inquiry_type = forms.ChoiceField(
        choices=INQUIRY_CHOICES,
        widget=forms.Select(attrs={'class': 'form-select'}),
        required=True
    )
    notes = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Optional details...'}),
        required=False
    )