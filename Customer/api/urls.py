from django.urls import path
from . import views

urlpatterns = [
    path('', views.storefront, name='storefront'),
    path('offers/', views.offer_list, name='offer_list'),
    path('referrals/', views.referral_list, name='referral_list'),
    path('referrals/create/', views.create_referral, name='create_referral'),
    path('payouts/setup/', views.onboard_cpa_stripe, name='onboard_cpa_stripe'),
    path('referrals/update-status/<int:pk>/', views.update_referral_status, name='update_referral_status'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
    path('verifier/', views.cpa_verifier, name='cpa_verifier'),
    path('verifier/approve/<int:pk>/', views.approve_cpa, name='approve_cpa'),
]
