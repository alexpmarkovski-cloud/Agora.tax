import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'customer_db.settings')
django.setup()

from api.models import FinancialCompany, ProductCategory, Product, Offer

c, _ = FinancialCompany.objects.get_or_create(name='PWM Partners (Demo)', integration_type='MANUAL')

p_ind, _ = ProductCategory.objects.get_or_create(name='Private Wealth Management', client_type='Individual')
p_bus, _ = ProductCategory.objects.get_or_create(name='Private Wealth Management', client_type='Business')

prod_ind, _ = Product.objects.get_or_create(company=c, category=p_ind, name='PWM Individual Strategy')
prod_bus, _ = Product.objects.get_or_create(company=c, category=p_bus, name='PWM Business Strategy')

Offer.objects.get_or_create(product=prod_ind, name='PWM Referral (Individual)', defaults={'cpa_payout': 1000, 'platform_fee': 500, 'client_bonus_summary': 'Tailored wealth plan', 'is_active': True})
Offer.objects.get_or_create(product=prod_bus, name='PWM Referral (Business)', defaults={'cpa_payout': 1500, 'platform_fee': 750, 'client_bonus_summary': 'Corporate wealth plan', 'is_active': True})

print("Successfully seeded Private Wealth Management categories and offers.")
