from django.db import models
from django.utils import timezone

# 1. Financial Companies (The Banks/Institutions)
class FinancialCompany(models.Model):
    name = models.CharField(max_length=255)
    logo_url = models.URLField(blank=True, null=True)
    integration_type = models.CharField(max_length=50, default='API') # e.g. API, MANUAL
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class ProductCategory(models.Model):
    CLIENT_TYPE_CHOICES = [
        ('Individual', 'Individual'),
        ('Business', 'Business'),
    ]
    client_type = models.CharField(max_length=50, choices=CLIENT_TYPE_CHOICES, default='Individual')
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.client_type} - {self.name}"
        
    class Meta:
        verbose_name_plural = "Product Categories"
        unique_together = ('name', 'client_type')

# 2. Products (e.g., "High Yield Savings Account")
class Product(models.Model):
    company = models.ForeignKey(FinancialCompany, on_delete=models.CASCADE, related_name='products', null=True, blank=True)
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True)
    
    def __str__(self):
        comp_name = self.company.name if self.company else "Unknown Company"
        return f"{self.name} ({comp_name})"

# 3. Offers (The Specific Deal: "Refer now for $50")
# We separate Product from Offer so you can change prices without deleting the product.
class Offer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    name = models.CharField(max_length=255) # e.g. "Q4 2025 Bonus"
    professional_name = models.CharField(max_length=255, blank=True, null=True, help_text="Optional name of the financial/legal professional.")
    
    # Pricing Configuration
    cpa_payout = models.DecimalField(max_digits=10, decimal_places=2) # What the CPA gets
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2) # What You get
    
    # Client Facing Details
    client_bonus_summary = models.CharField(max_length=255, default="", help_text="e.g., '$300 Cash Bonus'")
    client_requirements = models.TextField(default="", help_text="e.g., 'Must deposit $15k within 30 days.'")
    application_link = models.URLField(blank=True, null=True, help_text="The direct link to the bank's application page.")

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Display this offer on the storefront")
    requires_client_state = models.BooleanField(default=False, help_text="If checked, creating a referral for this offer routes the CPA to a State Selection page.")
    terms_url = models.URLField(blank=True)

    # Contact details for when a referral is generated
    contact_email = models.EmailField(blank=True, null=True, help_text="Optional contact email provided to the CPA upon referral generation.")
    contact_phone = models.CharField(max_length=20, blank=True, null=True, help_text="Optional contact phone provided to the CPA upon referral generation.")

    def __str__(self):
        return f"{self.name} - ${self.cpa_payout}"

from django.contrib.auth.models import User

# 4. CPA Users (The Tax Pros)
# Note: Later we will link this to Django's built-in User Authentication
class CPAUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, null=True, blank=True)
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30)
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=255) # Required now
    stripe_account_id = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

class CPALicense(models.Model):
    cpa = models.ForeignKey(CPAUser, on_delete=models.CASCADE, related_name='licenses')
    state = models.CharField(max_length=2, help_text='State (e.g., NY)')
    license_number = models.CharField(max_length=50, help_text='CPA License Number')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.state} - {self.license_number}'


# 4b. Financial Company Users (The Bankers/Advisors)
class FinancialUser(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='financial_user')
    company = models.ForeignKey(FinancialCompany, on_delete=models.CASCADE, related_name='financial_users')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.company.name})"



# 4f. Financial Professional Licenses
class FinancialLicense(models.Model):
    financial_user = models.ForeignKey(FinancialUser, on_delete=models.CASCADE, related_name='licenses')
    state = models.CharField(max_length=2, help_text='State registered (e.g., NY)')
    crd_number = models.CharField(max_length=50, help_text='Individual CRD Number')
    firm_crd = models.CharField(max_length=50, blank=True, null=True, help_text='Firm CRD/SEC Number')
    zip_code = models.CharField(max_length=20, blank=True, null=True, help_text='ZIP Code')
    is_active = models.BooleanField(default=True, help_text='CRD active status')
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.state} - {self.crd_number} (Active: {self.is_active})"



# 5. Referrals (The "Order")
# This is the most critical table. It snapshots the price.
class Referral(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONVERTED', 'Converted'),
        ('PAID', 'Paid'),
        ('REJECTED', 'Rejected'),
    ]

    FINANCIAL_PRO_STATUS_CHOICES = [
        ('NOT_VIEWED', 'Not Viewed'),
        ('VIEWED', 'Viewed'),
        ('CLIENT_CONTACTED', 'Client Contacted'),
    ]

    cpa = models.ForeignKey(CPAUser, on_delete=models.CASCADE, related_name='referrals', null=True, blank=True)
    financial_user = models.ForeignKey('FinancialUser', on_delete=models.CASCADE, related_name='made_referrals', null=True, blank=True)
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True) # If offer is deleted, keep the referral history
    # Link to Payout Batch
    payout_batch = models.ForeignKey('PayoutBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    # SNAPSHOT PRICING (The "Receipt")
    # We copy the price from the Offer to here when the referral is created.
    agreed_cpa_payout = models.DecimalField(max_digits=10, decimal_places=2)
    agreed_platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    client_name = models.CharField(max_length=255, blank=True, null=True)
    client_email = models.EmailField(blank=True, null=True) # Or hash this for privacy later
    client_phone = models.CharField(max_length=50, blank=True, null=True)
    client_state = models.CharField(max_length=2, blank=True, null=True, help_text="Used primarily for PWM")
    referral_code = models.CharField(max_length=50, blank=True, null=True, help_text="Generated for specific products like PWM")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    financial_pro_status = models.CharField(max_length=50, choices=FINANCIAL_PRO_STATUS_CHOICES, default='NOT_VIEWED')
    
    gen_date = models.DateTimeField(auto_now_add=True) # Creation date
    conversion_date = models.DateTimeField(null=True, blank=True)

    @property
    def referrer_name(self):
        if self.cpa:
            return f"{self.cpa.first_name} {self.cpa.last_name}"
        elif self.financial_user:
            return f"{self.financial_user.user.first_name} {self.financial_user.user.last_name}"
        return "Unknown Referrer"

    @property
    def referrer_company(self):
        if self.cpa:
            return self.cpa.company_name
        elif self.financial_user:
            return self.financial_user.company.name
        return ""

    @property
    def referrer_email(self):
        if self.cpa:
            return self.cpa.email
        elif self.financial_user:
            return self.financial_user.user.email
        return ""

    def __str__(self):
        return f"Referral #{self.id} by {self.referrer_name}"

# 6. Transactions (The Master Ledger)
# Replaces separate "Tax Payment" and "Finance Payment" tables
class Transaction(models.Model):
    PAYMENT_METHODS = [
        ('ACH', 'ACH Transfer'),
        ('WIRE', 'Wire Transfer'),
        ('CHECK', 'Check'),
        ('INTERNAL', 'Internal Adjustment'),
    ]
    
    PAYEE_TYPES = [
        ('CPA', 'CPA User'),
        ('AGORA', 'Agora Platform'),
        ('CLIENT', 'End Client'),
    ]

    referral = models.ForeignKey(Referral, on_delete=models.CASCADE, related_name='transactions')
    
    payee_type = models.CharField(max_length=20, choices=PAYEE_TYPES)
    payee_reference_id = models.IntegerField(help_text="ID of the CPA or System")
    
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    
    transaction_date = models.DateTimeField(default=timezone.now)
    status = models.CharField(max_length=50, default='PROCESSING')

# 7. Payout Batches (Monthly Groups)
class PayoutBatch(models.Model):
    STATUS_CHOICES = [
        ('OPEN', 'Open'),
        ('PROCESSING', 'Processing'),
        ('PAID', 'Paid'),
    ]

    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='OPEN')
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    reference_note = models.CharField(max_length=255, help_text="e.g. January 2026 Payouts")
    
    def __str__(self):
        return f"Batch #{self.id} - {self.reference_note} ({self.status})"

    def process_batch(self):
        # Prevent double processing
        if self.status == 'PAID':
            return
            
        print(f"--- STARTING BATCH #{self.id} PROCESSING ---")
        
        for referral in self.referrals.all():
            if referral.status == 'CONVERTED':
                amount = referral.agreed_cpa_payout
                cpa_stripe_id = referral.cpa.stripe_account_id or "NO_STRIPE_ID"
                
                # Placeholder Simulation
                print(f"SIMULATION: Transferring ${amount} from [PLACEHOLDER_BANK_ID] to CPA {cpa_stripe_id}")
                
                # Update Referral Status
                referral.status = 'PAID'
                referral.save()
        
        # Update Batch Status
        self.status = 'PAID'
        self.save()
        print(f"--- BATCH #{self.id} COMPLETED ---")