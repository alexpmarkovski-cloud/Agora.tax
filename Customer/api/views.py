from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import stripe
from .models import Referral, Offer, CPAUser, ProductCategory, CPALicense, FinancialUser, FinancialCompany, Product, FinancialLicense
from .forms import ReferralForm, UserUpdateForm, CPALicenseForm, ContactInquiryForm, FinancialSignupForm, OfferForm, FinancialLicenseForm
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
        return render(request, 'api/admin/referral_list.html', {'error': str(e)})

@login_required
def edit_profile(request):
    cpa = getattr(request.user, 'cpauser', None)
    financial_user = getattr(request.user, 'financial_user', None)
    
    if request.method == 'POST':
        if 'update_profile' in request.POST:
            form = UserUpdateForm(request.POST, instance=request.user)
            if form.is_valid():
                form.save()
                return redirect('edit_profile')
        elif 'add_license' in request.POST:
            if cpa:
                license_form = CPALicenseForm(request.POST)
                if license_form.is_valid():
                    license = license_form.save(commit=False)
                    license.cpa = cpa
                    license.save()
                    return redirect('edit_profile')
            elif financial_user:
                license_form = FinancialLicenseForm(request.POST)
                if license_form.is_valid():
                    license = license_form.save(commit=False)
                    license.financial_user = financial_user
                    license.save()
                    return redirect('edit_profile')
    
    form = UserUpdateForm(instance=request.user)
    
    if cpa:
        license_form = CPALicenseForm()
        licenses = cpa.licenses.all()
    elif financial_user:
        license_form = FinancialLicenseForm()
        licenses = financial_user.licenses.all()
    else:
        license_form = None
        licenses = []
    
    return render(request, 'api/shared/edit_profile.html', {
        'form': form,
        'license_form': license_form,
        'licenses': licenses,
        'cpa': cpa,
        'financial_user': financial_user
    })

import json

@login_required
def create_referral(request):
    cpa_user = getattr(request.user, 'cpauser', None)
    financial_user = getattr(request.user, 'financial_user', None)
    
    # Verification Check
    is_verified = False
    if cpa_user and cpa_user.licenses.filter(is_verified=True).exists():
        is_verified = True
    elif financial_user and financial_user.licenses.filter(is_verified=True).exists():
        is_verified = True
        
    if request.method == 'POST':
        if not is_verified:
            messages.error(request, "You must be verified or have an active license to create a referral.")
            return redirect('create_referral')
            
        form = ReferralForm(request.POST)
        if form.is_valid():
            referral = form.save(commit=False)
            if cpa_user:
                referral.cpa = cpa_user
            elif financial_user:
                referral.financial_user = financial_user
            offer = referral.offer
            referral.agreed_cpa_payout = offer.cpa_payout
            referral.agreed_platform_fee = offer.platform_fee
            
            # Check for State Requirements
            if offer.requires_client_state:
                # Stash details in session for step 2
                request.session['pwm_referral_data'] = {
                    'offer_id': offer.id,
                    'client_name': referral.client_name,
                    'client_email': referral.client_email,
                    'client_phone': referral.client_phone,
                }
                return redirect('pwm_state_selection')
                
            referral.save()
            messages.success(request, f"Referral created successfully for {offer.name}")
            
            if cpa_user:
                return redirect('cpa_dashboard')
            elif financial_user:
                return redirect('financial_dashboard')
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
    
    if cpa_user or financial_user:
        return render(request, 'api/cpa/create_referral.html', {
            'form': form,
            'catalog_json': json.dumps(catalog),
            'is_verified': is_verified
        })
    else:
        return render(request, 'api/cpa/create_referral.html', {
            'form': form,
            'error': "Error: Your account is not linked to a CPA or Financial profile."
        })

import random
import string

@login_required
def pwm_state_selection(request):
    cpa_user = getattr(request.user, 'cpauser', None)
    financial_user = getattr(request.user, 'financial_user', None)
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
            financial_user=financial_user,
            offer=offer,
            agreed_cpa_payout=offer.cpa_payout,
            agreed_platform_fee=offer.platform_fee,
            client_name=data.get('client_name', ''),
            client_email=data.get('client_email', ''),
            client_phone=data.get('client_phone', ''),
            client_state=state.upper(),
            referral_code=ref_code
        )
        
        del request.session['pwm_referral_data'] # Clean up
        
        return render(request, 'api/financial_pro/pwm_success.html', {'referral_code': ref_code, 'state': state.upper(), 'offer': offer})
        
    return render(request, 'api/financial_pro/pwm_state_selection.html')

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
        
    return render(request, 'api/shared/contact_support.html', {'form': form})

@staff_member_required
def referral_list(request):
    referrals = Referral.objects.all().order_by('-gen_date')
    
    category_id = request.GET.get('category')
    if category_id:
        referrals = referrals.filter(offer__product__category_id=category_id)
        
    categories = ProductCategory.objects.all().order_by('name')
    
    selected_category_id = int(category_id) if category_id and category_id.isdigit() else None
    
    return render(request, 'api/admin/referral_list.html', {
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
    return render(request, 'api/admin/cpa_verifier.html', {'unverified_licenses': unverified_licenses})

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

def landing_page(request):
    return render(request, 'api/shared/landing_page.html')

@staff_member_required
def financial_pro_verifier(request):
    unverified_licenses = FinancialLicense.objects.filter(is_verified=False).select_related('financial_user__user').order_by('-created_at')
    return render(request, 'api/admin/financial_pro_verifier.html', {'unverified_licenses': unverified_licenses})

@staff_member_required
def approve_financial_pro(request, pk):
    license = get_object_or_404(FinancialLicense, pk=pk)
    if request.method == 'POST':
        license.is_verified = True
        license.save()
        messages.success(request, f'Financial Pro License {license.crd_number} approved.')
    return redirect('financial_pro_verifier')

@staff_member_required
def reject_financial_pro(request, pk):
    license = get_object_or_404(FinancialLicense, pk=pk)
    if request.method == 'POST':
        # Send a placeholder rejection email
        subject = 'Update on your Financial Professional Account Registration'
        message = 'Thank you for registering. Unfortunately, we are unable to approve your account at this time. Please contact support for more information.'
        from_email = settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@agora.com'
        recipient_list = [license.financial_user.user.email]
        
        try:
            send_mail(subject, message, from_email, recipient_list)
            messages.success(request, f'Rejection email successfully sent to {license.financial_user.user.email}.')
        except Exception as e:
            messages.error(request, f'Failed to send rejection email: {str(e)}')
            
    return redirect('financial_pro_verifier')

from .services.finra_scraper import verify_financial_pro_finra

@staff_member_required
def auto_verify_financial_pro(request, pk):
    license = get_object_or_404(FinancialLicense, pk=pk)
    if request.method == 'POST':
        result = verify_financial_pro_finra(
            crd_number=license.crd_number,
            firm_crd=license.firm_crd,
            zip_code=license.zip_code
        )
        
        if result.get('is_valid'):
            license.is_verified = True
            license.save()
            messages.success(request, f"Auto-Verify Success: {result.get('message')}")
        else:
            messages.error(request, f"Auto-Verify Failed: {result.get('message')}")
            
    return redirect('financial_pro_verifier')

@login_required
def offer_list(request):
    offers = Offer.objects.filter(is_active=True).order_by('name')
    return render(request, 'api/shared/offer_list.html', {'offers': offers})

@login_required
def cpa_dashboard(request):
    cpa_user = getattr(request.user, 'cpauser', None)
    
    if not cpa_user:
        messages.error(request, "Your account is not linked to a CPA profile.")
        return redirect('landing_page')
        
    if request.method == 'POST':
        pass
    referrals = Referral.objects.filter(cpa=cpa_user).order_by('-gen_date')
    
    category_id = request.GET.get('category')
    if category_id:
        referrals = referrals.filter(offer__product__category_id=category_id)
        
    categories = ProductCategory.objects.all().order_by('name')
    selected_category_id = int(category_id) if category_id and category_id.isdigit() else None
    
    return render(request, 'api/cpa/cpa_dashboard.html', {
        'referrals': referrals,
        'categories': categories,
        'selected_category_id': selected_category_id
    })


from django.contrib.auth import login

@login_required
def login_redirect(request):
    if request.user.is_staff or request.user.is_superuser:
        return redirect('referral_list')
    elif hasattr(request.user, 'financial_user'):
        return redirect('financial_dashboard')
    elif hasattr(request.user, 'cpauser'):
        return redirect('cpa_dashboard')
    else:
        return redirect('landing_page')


def financial_signup(request):
    if request.user.is_authenticated:
        return redirect('login_redirect')
        
    if request.method == 'POST':
        form = FinancialSignupForm(request.POST)
        if form.is_valid():
            # Save standard User
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()
            
            company = form.cleaned_data.get('company')
            new_company_name = form.cleaned_data.get('new_company_name')

            if new_company_name:
                company, created = FinancialCompany.objects.get_or_create(name=new_company_name)

            # Save associated FinancialUser
            financial_user = FinancialUser.objects.create(
                user=user,
                company=company
            )

            # Create the initial FinancialLicense
            FinancialLicense.objects.create(
                financial_user=financial_user,
                state=form.cleaned_data['state_registered'].upper(),
                crd_number=form.cleaned_data['crd_number'],
                firm_crd=form.cleaned_data['firm_crd'],
                zip_code=form.cleaned_data['zip_code'],
                is_active=form.cleaned_data['crd_active']
            )
            
            # Automatically log the user in
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            messages.success(request, f"Welcome to the Agora Partner Portal, {user.first_name}!")
            return redirect('financial_dashboard')
    else:
        form = FinancialSignupForm()
        
    return render(request, 'api/financial_pro/financial_signup.html', {'form': form})


def financial_user_required(view_func):
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect('account_login')
        if not hasattr(request.user, 'financial_user'):
            messages.error(request, "Access denied: This portal is for Financial Professionals only.")
            return redirect('landing_page')
            
        # Check verification status
        financial_user = request.user.financial_user
        if not financial_user.licenses.filter(is_verified=True).exists():
            return render(request, 'api/shared/unverified_financial.html')
            
        return view_func(request, *args, **kwargs)
    return wrapper


@financial_user_required
def financial_dashboard(request):
    financial_user = request.user.financial_user
    company = financial_user.company
    
    # 1. Referee: Get all referrals for this company's offers
    referrals = Referral.objects.filter(offer__product__company=company).order_by('-gen_date')
    
    # Get all offers and products owned by this company
    offers = Offer.objects.filter(product__company=company).order_by('name')
    products = Product.objects.filter(company=company).order_by('name')
    
    # Calculate pipeline metrics
    converted_count = referrals.filter(status__in=['CONVERTED', 'PAID']).count()
    total_count = referrals.count()
    conversion_rate = round((converted_count / total_count * 100), 1) if total_count > 0 else 0
    
    # 2. Referrer: Get all referrals made by this financial advisor
    referrals_made = Referral.objects.filter(financial_user=financial_user).order_by('-gen_date')
    
    category_id = request.GET.get('category')
    if category_id:
        referrals_made = referrals_made.filter(offer__product__category_id=category_id)
        
    categories = ProductCategory.objects.all().order_by('name')
    selected_category_id = int(category_id) if category_id and category_id.isdigit() else None
    
    return render(request, 'api/financial_pro/financial_dashboard.html', {
        'company': company,
        'referrals': referrals,
        'offers': offers,
        'products': products,
        'converted_count': converted_count,
        'conversion_rate': conversion_rate,
        'referrals_made': referrals_made,
        'categories': categories,
        'selected_category_id': selected_category_id
    })



@financial_user_required
def create_offer(request):
    company = request.user.financial_user.company
    dashboard_url = 'financial_dashboard'
    
    if request.method == 'POST':
        form = OfferForm(request.POST, company=company)
        if form.is_valid():
            offer = form.save(commit=False)
            category = form.cleaned_data.get('category')
            product, created = Product.objects.get_or_create(
                name=category.name,
                category=category,
                company=company,
            )
            offer.product = product
            offer.cpa_payout = 0.00
            offer.platform_fee = 0.00
            offer.save()
            messages.success(request, f"Successfully published offer: {offer.name}")
            return redirect(dashboard_url)
    else:
        form = OfferForm(company=company)
        
    return render(request, 'api/financial_pro/offer_form.html', {
        'form': form,
        'action_name': 'Create New Offer',
        'company': company
    })

from .forms import ProductForm, ReferralStatusForm

@financial_user_required
def create_product(request):
    company = request.user.financial_user.company
    dashboard_url = 'financial_dashboard'
    
    if request.method == 'POST':
        form = ProductForm(request.POST)
        if form.is_valid():
            product = form.save(commit=False)
            product.company = company
            product.save()
            messages.success(request, f"Successfully created product: {product.name}")
            return redirect(dashboard_url)
    else:
        form = ProductForm()
        
    return render(request, 'api/financial_pro/product_form.html', {
        'form': form,
        'action_name': 'Create New Product',
        'company': company
    })

@financial_user_required
def financial_referrals(request):
    company = request.user.financial_user.company
    referrals = Referral.objects.filter(offer__product__company=company).order_by('-gen_date')
        
    return render(request, 'api/financial_pro/financial_referrals.html', {
        'referrals': referrals,
        'company': company,
        'status_choices': Referral.FINANCIAL_PRO_STATUS_CHOICES
    })

from django.views.decorators.http import require_POST

@financial_user_required
@require_POST
def update_financial_pro_status(request, pk):
    company = request.user.financial_user.company
    referral = get_object_or_404(Referral, pk=pk, offer__product__company=company)
        
    form = ReferralStatusForm(request.POST, instance=referral)
    if form.is_valid():
        form.save()
        messages.success(request, f"Status updated for Referral #{referral.id}")
    else:
        messages.error(request, "Failed to update status.")
    return redirect('financial_referrals')


@financial_user_required
def edit_offer(request, pk):
    company = request.user.financial_user.company
    dashboard_url = 'financial_dashboard'
    offer = get_object_or_404(Offer, pk=pk)
    
    # Verify ownership
    offer_company = offer.product.legal_company if is_legal else offer.product.company
    if offer_company != company:
        messages.error(request, "Access denied: You do not have permission to edit this offer.")
        return redirect(dashboard_url)
        
    if request.method == 'POST':
        form = OfferForm(request.POST, instance=offer, company=company)
        if form.is_valid():
            offer = form.save(commit=False)
            category = form.cleaned_data.get('category')
            product, created = Product.objects.get_or_create(
                name=category.name,
                category=category,
                company=company,
            )
            offer.product = product
            offer.cpa_payout = 0.00
            offer.platform_fee = 0.00
            offer.save()
            messages.success(request, f"Successfully updated offer: {offer.name}")
            return redirect(dashboard_url)
    else:
        form = OfferForm(instance=offer, company=company)
        
    return render(request, 'api/financial_pro/offer_form.html', {
        'form': form,
        'action_name': f"Edit Offer: {offer.name}",
        'company': company,
        'offer': offer
    })


@financial_user_required
def financial_update_referral(request, pk):
    company = request.user.financial_user.company
    dashboard_url = 'financial_dashboard'
    referral = get_object_or_404(Referral, pk=pk)
    
    # Verify ownership
    referral_company = referral.offer.product.legal_company if is_legal else referral.offer.product.company
    if referral_company != company:
        messages.error(request, "Access denied: You do not have permission to manage this referral.")
        return redirect(dashboard_url)
        
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'approve':
            referral.status = 'CONVERTED'
            referral.save()
            messages.success(request, f"Referral #{referral.id} has been marked as Converted!")
        elif action == 'reject':
            referral.status = 'REJECTED'
            referral.save()
            messages.success(request, f"Referral #{referral.id} has been marked as Rejected.")
            
    return redirect(dashboard_url)


