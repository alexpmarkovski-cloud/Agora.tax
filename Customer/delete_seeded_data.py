import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'customer_db.settings')
django.setup()

from api.models import FinancialCompany, Product, Offer, Referral, FinancialUser

print("Deleting all referrals...")
Referral.objects.all().delete()

print("Deleting all financial users...")
FinancialUser.objects.all().delete()

print("Deleting all offers...")
Offer.objects.all().delete()

print("Deleting all products...")
Product.objects.all().delete()

print("Deleting all financial companies...")
FinancialCompany.objects.all().delete()

print("Pruning finished! All financial companies, products, offers, and associated referrals/users have been completely deleted from your PostgreSQL database.")
