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
    company = models.ForeignKey(FinancialCompany, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    category = models.ForeignKey(ProductCategory, on_delete=models.SET_NULL, null=True, related_name='products')
    description = models.TextField(blank=True)
    
    def __str__(self):
        return f"{self.name} ({self.company.name})"

# 3. Offers (The Specific Deal: "Refer now for $50")
# We separate Product from Offer so you can change prices without deleting the product.
class Offer(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='offers')
    name = models.CharField(max_length=255) # e.g. "Q4 2025 Bonus"
    
    # Pricing Configuration
    cpa_payout = models.DecimalField(max_digits=10, decimal_places=2) # What the CPA gets
    platform_fee = models.DecimalField(max_digits=10, decimal_places=2) # What You get
    
    # Client Facing Details
    client_bonus_summary = models.CharField(max_length=255, default="", help_text="e.g., '$300 Cash Bonus'")
    client_requirements = models.TextField(default="", help_text="e.g., 'Must deposit $15k within 30 days.'")
    application_link = models.URLField(blank=True, null=True, help_text="The direct link to the bank's application page.")

    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False, help_text="Display this offer on the storefront")
    terms_url = models.URLField(blank=True)

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
        

# 5. Referrals (The "Order")
# This is the most critical table. It snapshots the price.
class Referral(models.Model):
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('CONVERTED', 'Converted'),
        ('PAID', 'Paid'),
        ('REJECTED', 'Rejected'),
    ]

    cpa = models.ForeignKey(CPAUser, on_delete=models.CASCADE, related_name='referrals')
    offer = models.ForeignKey(Offer, on_delete=models.SET_NULL, null=True) # If offer is deleted, keep the referral history
    # Link to Payout Batch
    payout_batch = models.ForeignKey('PayoutBatch', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    
    # SNAPSHOT PRICING (The "Receipt")
    # We copy the price from the Offer to here when the referral is created.
    agreed_cpa_payout = models.DecimalField(max_digits=10, decimal_places=2)
    agreed_platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    client_email = models.EmailField(blank=True, null=True) # Or hash this for privacy later
    client_state = models.CharField(max_length=2, blank=True, null=True, help_text="Used primarily for PWM")
    referral_code = models.CharField(max_length=50, blank=True, null=True, help_text="Generated for specific products like PWM")
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    
    gen_date = models.DateTimeField(auto_now_add=True) # Creation date
    conversion_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Referral #{self.id} by {self.cpa.first_name} {self.cpa.last_name}"

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