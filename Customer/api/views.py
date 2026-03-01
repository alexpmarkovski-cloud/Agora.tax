from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.conf import settings
import stripe
from .models import Referral, Offer, CPAUser, ProductCategory, CPALicense
from .forms import ReferralForm, UserUpdateForm, CPALicenseForm

# Global Stripe Setup
stripe.api_key = settings.STRIPE_SECRET_KEY

@login_required
def onboard_cpa_stripe(request):
    try:
        # Get the CPA profile (assuming 1-to-1 link with User, but here we scan first())
        # Ideally, we should link User to CPAUser. For now, we take request.user.cpauser if exists
        cpa_user = getattr(request.user, 'cpauser', None)
        
        # Fallback for testing layouts if simple User isn't linked
        if not cpa_user:
             # Just for safety in dev: return error or grab first
             return redirect('referral_list')

        # Step A: Create Stripe Account if not exists
        if not cpa_user.stripe_account_id:
            account = stripe.Account.create(
                type='express',
                country='US',
                email=cpa_user.email,
                capabilities={
                    'card_payments': {'requested': True},
                    'transfers': {'requested': True},
                },
            )
            cpa_user.stripe_account_id = account.id
            cpa_user.save()
        
        # Step B: Create Account Link
        account_link = stripe.AccountLink.create(
            account=cpa_user.stripe_account_id,
            refresh_url=request.build_absolute_uri(), # Retry this view
            return_url=request.build_absolute_uri('/'), # Back to dashboard
            type='account_onboarding',
        )
        
        return redirect(account_link.url)
        
    except Exception as e:
        # In prod, log this error
        return render(request, 'api/referral_list.html', {'error': str(e)})

@login_required
def edit_profile(request):
    cpa = getattr(request.user, 'cpauser', None)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = UserUpdateForm(request.POST, instance=request.user)
            license_form = CPALicenseForm()
            if form.is_valid():
                form.save()
                return redirect('edit_profile')
        elif 'add_license' in request.POST and cpa:
            form = UserUpdateForm(instance=request.user)
            license_form = CPALicenseForm(request.POST)
            if license_form.is_valid():
                license = license_form.save(commit=False)
                license.cpa = cpa
                license.save()
                return redirect('edit_profile')
    else:
        form = UserUpdateForm(instance=request.user)
        license_form = CPALicenseForm()
    
    licenses = cpa.licenses.all() if cpa else []
    
    return render(request, 'api/edit_profile.html', {
        'form': form,
        'license_form': license_form,
        'licenses': licenses,
        'cpa': cpa
    })

@login_required
def create_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            referral = form.save(commit=False)
            # Snapshot pricing from the offer
            if hasattr(request.user, 'cpauser'):
                referral.cpa = request.user.cpauser
            else:
                return render(request, 'api/create_referral.html', {
                    'form': form,
                    'error': "Error: Your account is not linked to a CPA profile."
                })
            
            offer = referral.offer
            referral.agreed_cpa_payout = offer.cpa_payout
            referral.agreed_platform_fee = offer.platform_fee
            referral.save()
            return redirect('referral_list')
    else:
        form = ReferralForm()
    return render(request, 'api/create_referral.html', {'form': form})

def referral_list(request):
    referrals = Referral.objects.all().order_by('-gen_date')
    
    category_id = request.GET.get('category')
    if category_id:
        referrals = referrals.filter(offer__product__category_id=category_id)
        
    categories = ProductCategory.objects.all().order_by('name')
    
    selected_category_id = int(category_id) if category_id and category_id.isdigit() else None
    
    return render(request, 'api/referral_list.html', {
        'referrals': referrals,
        'categories': categories,
        'selected_category_id': selected_category_id
    })

def update_referral_status(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    if request.method == 'POST':
        referral.status = 'CONVERTED'
        referral.save()
    return redirect('referral_list')

from django.contrib.admin.views.decorators import staff_member_required

@staff_member_required
def cpa_verifier(request):
    unverified_cpas = CPAUser.objects.filter(is_verified=False).order_by('-created_at')
    return render(request, 'api/cpa_verifier.html', {'unverified_cpas': unverified_cpas})

@staff_member_required
def approve_cpa(request, pk):
    cpa = get_object_or_404(CPAUser, pk=pk)
    if request.method == 'POST':
        cpa.is_verified = True
        cpa.save()
    return redirect('cpa_verifier')

@login_required
def storefront(request):
    featured_offers = Offer.objects.filter(is_active=True, is_featured=True)[:3]
    return render(request, 'api/storefront.html', {'featured_offers': featured_offers})

@login_required
def offer_list(request):
    offers = Offer.objects.filter(is_active=True).order_by('name')
    return render(request, 'api/offer_list.html', {'offers': offers})

