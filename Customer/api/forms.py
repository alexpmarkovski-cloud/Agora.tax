from django import forms
from django.contrib.auth.models import User
from allauth.account.forms import SignupForm
import threading
from .models import Referral, Offer, CPAUser, CPALicense, ProductCategory, FinancialLicense
from .services.nasba_scraper import verify_cpa_nasba

class CPASignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label='First Name')
    last_name = forms.CharField(max_length=30, label='Last Name')
    company_name = forms.CharField(max_length=255, label='Company Name')
    license_number = forms.CharField(max_length=50, label='CPA License Number')
    license_state = forms.CharField(max_length=2, label='License State (e.g., NY)')
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'd-none', 'autocomplete': 'off', 'tabindex': '-1'}), label="")

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:
            raise forms.ValidationError("Anti-spam protection triggered.")
        return website

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
    client_name = forms.CharField(
        max_length=255,
        required=True,
        label="Client Name",
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., John Doe'})
    )
    client_type = forms.ChoiceField(
        choices=[('', 'Select Client Type'), ('Individual', 'Individual'), ('Business', 'Business')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    category = forms.ChoiceField(
        choices=[('', 'Select Category')],
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    consent = forms.BooleanField(
        required=True,
        label="I confirm that I have this client's explicit consent to share their contact information with the selected financial professional.",
        widget=forms.CheckboxInput(attrs={'class': 'form-check-input'})
    )

    class Meta:
        model = Referral
        fields = ['client_type', 'category', 'offer', 'client_name', 'client_email', 'client_phone']
        widgets = {
            'offer': forms.Select(attrs={'class': 'form-select'}),
            'client_email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'e.g., john@example.com'}),
            'client_phone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., (555) 019-2834'}),
        }
        labels = {
            'client_email': 'Client Email Address',
            'client_phone': 'Client Phone Number',
        }

    # This ensures users can't pick "Dead" offers
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['offer'].queryset = Offer.objects.filter(is_active=True)
        self.fields['offer'].required = True
        self.fields['offer'].label_from_instance = self.label_from_instance
        
        # Dynamically load category choices from database
        self.fields['category'].choices = [('', 'Select Category')] + [
            (cat.name, cat.name) for cat in ProductCategory.objects.all()
        ]

    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('client_email')
        phone = cleaned_data.get('client_phone')

        if not email and not phone:
            raise forms.ValidationError(
                "You must provide at least one contact method: either a Phone Number or an Email Address is required."
            )
        return cleaned_data

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
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'd-none', 'autocomplete': 'off', 'tabindex': '-1'}), label="")

    def clean_website(self):
        website = self.cleaned_data.get('website')
        if website:
            raise forms.ValidationError("Anti-spam protection triggered.")
        return website


from .models import FinancialCompany, Product

class FinancialSignupForm(forms.ModelForm):
    password = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Password'}))
    password_confirm = forms.CharField(widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirm Password'}), label="Confirm Password")
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'First Name'}))
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Last Name'}))
    company = forms.ModelChoiceField(
        queryset=FinancialCompany.objects.all(),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Financial Institution / Company",
        required=False
    )
    new_company_name = forms.CharField(
        max_length=255, 
        required=False, 
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter your institution name'}),
        label="Or Add New Institution"
    )
    crd_number = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Individual CRD Number'}), label="Individual CRD Number")
    firm_crd = forms.CharField(max_length=50, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Firm CRD/SEC Number'}), label="Firm CRD/SEC Number")
    zip_code = forms.CharField(max_length=20, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}), label="ZIP Code")
    state_registered = forms.CharField(max_length=2, widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g. NY'}), label="State Registered")
    crd_active = forms.BooleanField(required=False, initial=True, widget=forms.CheckboxInput(attrs={'class': 'form-check-input'}), label="CRD Number Active")
    website = forms.CharField(required=False, widget=forms.TextInput(attrs={'class': 'd-none', 'autocomplete': 'off', 'tabindex': '-1'}), label="")

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'company']
        widgets = {
            'username': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Username'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Email Address'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password_confirm = cleaned_data.get("password_confirm")
        company = cleaned_data.get("company")
        new_company_name = cleaned_data.get("new_company_name")
        website = cleaned_data.get("website")

        if website:
            raise forms.ValidationError("Anti-spam protection triggered.")

        if password and password_confirm and password != password_confirm:
            self.add_error('password_confirm', "Passwords do not match.")
            
        if not company and not new_company_name:
            raise forms.ValidationError("You must either select an existing institution or enter a new one.")
            
        if company and new_company_name:
            raise forms.ValidationError("Please select an existing institution OR enter a new one, but not both.")

        email = cleaned_data.get("email")
        if email and User.objects.filter(email=email).exists():
            self.add_error('email', "A user with this email already exists.")
            
        return cleaned_data


class OfferForm(forms.ModelForm):
    category = forms.ModelChoiceField(
        queryset=ProductCategory.objects.all().order_by('name'),
        widget=forms.Select(attrs={'class': 'form-select'}),
        label="Target Product",
        required=True,
        empty_label="Select a Product..."
    )

    class Meta:
        model = Offer
        fields = [
            'name', 'professional_name',
            'client_bonus_summary', 'client_requirements',
            'application_link', 'terms_url', 'is_active',
            'contact_email', 'contact_phone'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., Q4 Promo'}),
            'professional_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., John Smith (Optional)'}),
            'client_bonus_summary': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., $300 Cash Bonus'}),
            'client_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'e.g., Deposit $10k...'}),
            'application_link': forms.URLInput(attrs={'class': 'form-control'}),
            'terms_url': forms.URLInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contact_email': forms.EmailInput(attrs={'class': 'form-control'}),
            'contact_phone': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        
        if self.instance and self.instance.pk and self.instance.product and self.instance.product.category:
            self.fields['category'].initial = self.instance.product.category

class ProductForm(forms.ModelForm):
    class Meta:
        model = Product
        fields = ['name', 'category', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., High Yield Savings'}),
            'category': forms.Select(attrs={'class': 'form-select'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

class ReferralStatusForm(forms.ModelForm):
    class Meta:
        model = Referral
        fields = ['financial_pro_status']
        widgets = {
            'financial_pro_status': forms.Select(attrs={'class': 'form-select form-select-sm', 'onchange': 'this.form.submit()'})
        }

class FinancialLicenseForm(forms.ModelForm):
    class Meta:
        model = FinancialLicense
        fields = ['state', 'crd_number', 'firm_crd', 'zip_code', 'is_active']
        widgets = {
            'state': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'e.g., NY'}),
            'crd_number': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Individual CRD Number'}),
            'firm_crd': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Firm CRD/SEC Number'}),
            'zip_code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'ZIP Code'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }