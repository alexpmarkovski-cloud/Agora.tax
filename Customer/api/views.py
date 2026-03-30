from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import stripe
from .models import Referral, Offer, CPAUser, ProductCategory, CPALicense
from .forms import ReferralForm, UserUpdateForm, CPALicenseForm, ContactInquiryForm
from django.contrib.admin.views.decorators import staff_member_required

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

import json

@login_required
def create_referral(request):
    cpa_user = getattr(request.user, 'cpauser', None)
    
    # Verification Check
    is_verified = False
    if cpa_user and cpa_user.licenses.filter(is_verified=True).exists():
        is_verified = True
        
    if request.method == 'POST':
        if not is_verified:
            messages.error(request, "You must be verified to create a referral.")
            return redirect('create_referral')
            
        form = ReferralForm(request.POST)
        if form.is_valid():
            referral = form.save(commit=False)
            referral.cpa = cpa_user
            offer = referral.offer
            referral.agreed_cpa_payout = offer.cpa_payout
            referral.agreed_platform_fee = offer.platform_fee
            
            # Check for State Requirements
            if offer.requires_client_state:
                # Stash details in session for step 2
                request.session['pwm_referral_data'] = {
                    'offer_id': offer.id,
                    'client_email': referral.client_email,
                }
                return redirect('pwm_state_selection')
                
            referral.save()
            messages.success(request, f"Referral created successfully for {offer.name}")
            return redirect('cpa_dashboard')
    else:
        form = ReferralForm()
        
    # Generate the catalog JSON for dynamic dropdowns
    active_offers = Offer.objects.filter(is_active=True).select_related('product__category')
    catalog = {
        'Individual': {},
        'Business': {}
    }
    
    for offer in active_offers:
        cat = offer.product.category
        if cat:
            client_type = cat.client_type
            cat_name = cat.name
            
            if client_type in catalog:
                if cat_name not in catalog[client_type]:
                    catalog[client_type][cat_name] = []
                
                catalog[client_type][cat_name].append({
                    'id': offer.id,
                    'text': f"{offer.name} - Client Gets: {offer.client_bonus_summary}"
                })
                
    return render(request, 'api/create_referral.html', {
        'form': form,
        'catalog_json': json.dumps(catalog),
        'is_verified': is_verified
    })

import random
import string

@login_required
def pwm_state_selection(request):
    cpa_user = getattr(request.user, 'cpauser', None)
    if 'pwm_referral_data' not in request.session:
        messages.error(request, "Invalid PWM flow.")
        return redirect('create_referral')
        
    if request.method == 'POST':
        state = request.POST.get('state')
        if not state:
            messages.error(request, "State is required.")
            return redirect('pwm_state_selection')
            
        data = request.session['pwm_referral_data']
        offer = get_object_or_404(Offer, id=data['offer_id'])
        
        # Generate Referral Code e.g., PWM-NY-1234
        random_suffix = ''.join(random.choices(string.digits, k=4))
        ref_code = f"PWM-{state.upper()}-{random_suffix}"
        
        # Save Referral
        referral = Referral.objects.create(
            cpa=cpa_user,
            offer=offer,
            agreed_cpa_payout=offer.cpa_payout,
            agreed_platform_fee=offer.platform_fee,
            client_email=data.get('client_email', ''),
            client_state=state.upper(),
            referral_code=ref_code
        )
        
        del request.session['pwm_referral_data'] # Clean up
        
        return render(request, 'api/pwm_success.html', {'referral_code': ref_code, 'state': state.upper()})
        
    return render(request, 'api/pwm_state_selection.html')

@login_required
def contact_support(request):
    if request.method == 'POST':
        form = ContactInquiryForm(request.POST)
        if form.is_valid():
            inquiry_type = form.cleaned_data['inquiry_type']
            notes = form.cleaned_data['notes']
            
            subject = f"Support Inquiry: {inquiry_type} - {request.user.email}"
            message = f"User: {request.user.email}\nType: {inquiry_type}\n\nNotes:\n{notes}"
            
            # Send email
            try:
                # Placeholder admin email, using DEFAULT_FROM_EMAIL temporarily
                # Replace 'admin@agora.com' with an actual recipient when going to production
                recipient = 'admin@agora.com' 
                send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient])
                messages.success(request, "Your inquiry has been sent to our support team.")
                return redirect('cpa_dashboard')
            except Exception as e:
                messages.error(request, f"Failed to send inquiry: {e}")
    else:
        form = ContactInquiryForm()
        
    return render(request, 'api/contact_support.html', {'form': form})

@staff_member_required
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

@staff_member_required
def update_referral_status(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    if request.method == 'POST':
        referral.status = 'CONVERTED'
        referral.save()
    return redirect('referral_list')

@staff_member_required
def cpa_verifier(request):
    unverified_licenses = CPALicense.objects.filter(is_verified=False).select_related('cpa').order_by('-created_at')
    return render(request, 'api/cpa_verifier.html', {'unverified_licenses': unverified_licenses})

@staff_member_required
def approve_cpa(request, pk):
    license = get_object_or_404(CPALicense, pk=pk)
    if request.method == 'POST':
        license.is_verified = True
        license.save()
        messages.success(request, f'CPA License {license.license_number} approved.')
    return redirect('cpa_verifier')

@staff_member_required
def reject_cpa(request, pk):
    license = get_object_or_404(CPALicense, pk=pk)
    if request.method == 'POST':
        # Send a placeholder rejection email
        subject = 'Update on your CPA Account Registration'
        message = 'Thank you for registering. Unfortunately, we are unable to approve your account at this time. Please contact support for more information.'
        from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@agora.com'
        recipient_list = [license.cpa.email]
        
        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, f'Rejection email successfully sent to {license.cpa.email}.')
        except Exception as e:
            messages.error(request, f'Failed to send rejection email: {str(e)}')
            
    return redirect('cpa_verifier')

import threading
from .services.nasba_scraper import verify_cpa_nasba

@staff_member_required
def auto_verify_cpa(request, pk):
    license = get_object_or_404(CPALicense, pk=pk)
    if request.method == 'POST':
        cpa = license.cpa
        # Run synchronously for admin trigger so they get immediate feedback
        result = verify_cpa_nasba(
            first_name=cpa.first_name,
            last_name=cpa.last_name,
            state=license.state,
            license_number=license.license_number
        )
        
        if result.get('is_valid'):
            license.is_verified = True
            license.save()
            messages.success(request, f"Auto-Verify Success: {result.get('message')}")
        else:
            messages.error(request, f"Auto-Verify Failed: {result.get('message')}")
            
    return redirect('cpa_verifier')

@login_required
def storefront(request):
    featured_offers = Offer.objects.filter(is_active=True, is_featured=True)[:3]
    return render(request, 'api/storefront.html', {'featured_offers': featured_offers})

@login_required
def offer_list(request):
    offers = Offer.objects.filter(is_active=True).order_by('name')
    return render(request, 'api/offer_list.html', {'offers': offers})

@login_required
def cpa_dashboard(request):
    cpa_user = getattr(request.user, 'cpauser', None)
    
    if not cpa_user:
        messages.error(request, "Your account is not linked to a CPA profile.")
        return redirect('storefront')

    referrals = Referral.objects.filter(cpa=cpa_user).order_by('-gen_date')
    
    category_id = request.GET.get('category')
    if category_id:
        referrals = referrals.filter(offer__product__category_id=category_id)
        
    categories = ProductCategory.objects.all().order_by('name')
    selected_category_id = int(category_id) if category_id and category_id.isdigit() else None
    
    return render(request, 'api/cpa_dashboard.html', {
        'referrals': referrals,
        'categories': categories,
        'selected_category_id': selected_category_id
    })

