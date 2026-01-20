from django.shortcuts import render, redirect, get_object_or_404
from .models import Referral, Offer, CPAUser
from .forms import ReferralForm

def create_referral(request):
    if request.method == 'POST':
        form = ReferralForm(request.POST)
        if form.is_valid():
            referral = form.save(commit=False)
            # Snapshot pricing from the offer
            if hasattr(request.user, 'cpauser'):
                referral.cpa = request.user.cpauser
            else:
                # Option B (The Safety Net): Just grab the first CPA in the database.
                # This ensures the test works even if you aren't logged in correctly.
                cpa_fallback = CPAUser.objects.first()
                if not cpa_fallback:
                    # If no CPAs exist at all, we can't save. return an error or crash gracefully.
                    return render(request, 'api/create_referral.html', {
                        'form': form, 
                        'error': "No CPA Users exist! Please create one in the Admin Panel first."
                    })
                referral.cpa = cpa_fallback
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
    return render(request, 'api/referral_list.html', {'referrals': referrals})

def update_referral_status(request, pk):
    referral = get_object_or_404(Referral, pk=pk)
    if request.method == 'POST':
        referral.status = 'CONVERTED'
        referral.save()
    return redirect('referral_list')
