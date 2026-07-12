from django.contrib import admin
from django.db.models import Sum
from django.contrib import messages
from .models import FinancialCompany, ProductCategory, Product, Offer, CPAUser, CPALicense, Referral, Transaction, PayoutBatch, FinancialUser, FinancialLicense

class FinancialLicenseInline(admin.TabularInline):
    model = FinancialLicense
    extra = 0

@admin.register(FinancialUser)
class FinancialUserAdmin(admin.ModelAdmin):
    list_display = ('user', 'company', 'created_at')
    search_fields = ('user__username', 'user__email', 'company__name')
    inlines = [FinancialLicenseInline]

@admin.register(FinancialLicense)
class FinancialLicenseAdmin(admin.ModelAdmin):
    list_display = ('financial_user', 'state', 'crd_number', 'is_active')
    list_filter = ('state', 'is_active')
    search_fields = ('financial_user__user__username', 'crd_number')

@admin.register(FinancialCompany)
class FinancialCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'integration_type', 'created_at')
    search_fields = ('name',)

@admin.register(ProductCategory)
class ProductCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_type')
    list_filter = ('client_type',)
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'category')
    list_filter = ('company', 'category__client_type', 'category')
    search_fields = ('name', 'company__name')

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'cpa_payout', 'is_active', 'is_featured', 'requires_client_state')
    list_filter = ('is_active', 'is_featured', 'requires_client_state', 'product__company')
    list_editable = ('is_active', 'is_featured', 'requires_client_state')
    search_fields = ('name', 'product__name')
    fieldsets = (
        ('Basic Information', {
            'fields': ('product', 'name', 'is_active', 'is_featured', 'requires_client_state')
        }),
        ('Pricing Configuration', {
            'fields': ('cpa_payout', 'platform_fee')
        }),
        ('Client Facing Details', {
            'fields': ('client_bonus_summary', 'client_requirements', 'application_link', 'terms_url')
        }),
        ('Contact Information (e.g. for PWM)', {
            'fields': ('contact_email', 'contact_phone')
        }),
    )

class CPALicenseInline(admin.TabularInline):
    model = CPALicense
    extra = 0

@admin.register(CPAUser)
class CPAUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'company_name')
    search_fields = ('first_name', 'last_name', 'email', 'company_name')
    inlines = [CPALicenseInline]

@admin.action(description='Create Payout Batch from Selected')
def create_batch_from_referrals(modeladmin, request, queryset):
    # 1. Validation: Ensure no referrals are already in a batch
    if queryset.filter(payout_batch__isnull=False).exists():
        modeladmin.message_user(request, "Error: One or more selected referrals are already in a batch.", level=messages.ERROR)
        return

    # 2. Validation: Ensure all are CONVERTED
    if queryset.exclude(status='CONVERTED').exists():
        modeladmin.message_user(request, "Error: You can only batch referrals that are 'CONVERTED'.", level=messages.ERROR)
        return

    # 3. Create the Batch
    total_payout = queryset.aggregate(Sum('agreed_cpa_payout'))['agreed_cpa_payout__sum'] or 0
    
    batch = PayoutBatch.objects.create(
        total_amount=total_payout,
        reference_note=f"Manual Batch created by {request.user} on {queryset.first().gen_date.strftime('%Y-%m-%d')}"
    )
    
    # 4. Link Referrals
    queryset.update(payout_batch=batch)
    
    modeladmin.message_user(request, f"Success! Batch #{batch.id} created for {queryset.count()} referrals. Total: ${total_payout}")

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('id', 'cpa', 'offer', 'status', 'gen_date', 'payout_batch')
    list_filter = ('status', 'gen_date', 'payout_batch')
    search_fields = ('cpa__first_name', 'cpa__last_name', 'client_email')
    actions = [create_batch_from_referrals]

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'referral', 'payee_type', 'amount', 'method', 'status', 'transaction_date')
    list_filter = ('status', 'method', 'payee_type')
    search_fields = ('referral__id', 'payee_reference_id')

@admin.register(PayoutBatch)
class PayoutBatchAdmin(admin.ModelAdmin):
    list_display = ('id', 'reference_note', 'status', 'total_amount', 'created_at')
    list_filter = ('status',)
    actions = ['process_selected_batches']

    @admin.action(description="Process Selected Batches (Simulation)")
    def process_selected_batches(self, request, queryset):
        for batch in queryset:
            batch.process_batch()
        self.message_user(request, f"Processed {queryset.count()} batches.")
