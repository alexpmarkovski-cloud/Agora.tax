from django.contrib import admin
from django.db.models import Sum
from django.contrib import messages
from .models import FinancialCompany, Product, Offer, CPAUser, Referral, Transaction, PayoutBatch

@admin.register(FinancialCompany)
class FinancialCompanyAdmin(admin.ModelAdmin):
    list_display = ('name', 'integration_type', 'created_at')
    search_fields = ('name',)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'category')
    list_filter = ('company', 'category')
    search_fields = ('name', 'company__name')

@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    list_display = ('name', 'product', 'cpa_payout', 'client_bonus_summary', 'is_active', 'is_featured')
    list_filter = ('is_active', 'is_featured', 'product__company')
    list_editable = ('is_active', 'is_featured')
    search_fields = ('name', 'product__name')

@admin.register(CPAUser)
class CPAUserAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'email', 'company_name', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('first_name', 'last_name', 'email', 'company_name')

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
    search_fields = ('cpa__name', 'client_email')
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
