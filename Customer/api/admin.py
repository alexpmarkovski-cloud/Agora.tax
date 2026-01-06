from django.contrib import admin
from .models import FinancialCompany, Product, Offer, CPAUser, Referral, Transaction

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
    list_display = ('name', 'product', 'cpa_payout', 'platform_fee', 'is_active')
    list_filter = ('is_active', 'product__company')
    search_fields = ('name', 'product__name')

@admin.register(CPAUser)
class CPAUserAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'company_name', 'is_verified')
    list_filter = ('is_verified',)
    search_fields = ('name', 'email', 'company_name')

@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    list_display = ('id', 'cpa', 'offer', 'status', 'gen_date')
    list_filter = ('status', 'gen_date')
    search_fields = ('cpa__name', 'client_email')

@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'referral', 'payee_type', 'amount', 'method', 'status', 'transaction_date')
    list_filter = ('status', 'method', 'payee_type')
    search_fields = ('referral__id', 'payee_reference_id')
