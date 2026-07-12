import os
from django.conf import settings
from api.models import CPAUser

print("=== Stripe Info in Settings ===")
print("PUBLISHABLE_KEY:", getattr(settings, 'STRIPE_PUBLISHABLE_KEY', 'Not found'))
print("SECRET_KEY:", getattr(settings, 'STRIPE_SECRET_KEY', 'Not found'))

print("\n=== Stripe Info in Database ===")
try:
    cpa_users = CPAUser.objects.exclude(stripe_account_id__isnull=True).exclude(stripe_account_id='')
    if cpa_users.exists():
        for user in cpa_users:
            print(f"User ID: {user.id}, Stripe Account ID: {user.stripe_account_id}")
    else:
        print("No stripe accounts found in DB.")
except Exception as e:
    print("Error querying CPAUser:", e)
