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

# 2. Products (e.g., "High Yield Savings Account")
class Product(models.Model):
    company = models.ForeignKey(FinancialCompany, on_delete=models.CASCADE, related_name='products')
    name = models.CharField(max_length=255)
    category = models.CharField(max_length=100) # e.g. 'IRA', 'Savings'
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
    
    is_active = models.BooleanField(default=True)
    terms_url = models.URLField(blank=True)

    def __str__(self):
        return f"{self.name} - ${self.cpa_payout}"

# 4. CPA Users (The Tax Pros)
# Note: Later we will link this to Django's built-in User Authentication
class CPAUser(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    company_name = models.CharField(max_length=255, blank=True)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

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
    
    # SNAPSHOT PRICING (The "Receipt")
    # We copy the price from the Offer to here when the referral is created.
    agreed_cpa_payout = models.DecimalField(max_digits=10, decimal_places=2)
    agreed_platform_fee = models.DecimalField(max_digits=10, decimal_places=2)
    
    client_email = models.EmailField(blank=True, null=True) # Or hash this for privacy later
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='PENDING')
    
    gen_date = models.DateTimeField(auto_now_add=True) # Creation date
    conversion_date = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Referral #{self.id} by {self.cpa.name}"

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