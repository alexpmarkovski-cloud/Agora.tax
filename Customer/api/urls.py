from django.urls import path
from . import views

urlpatterns = [
    path('', views.referral_list, name='referral_list'),
    path('create/', views.create_referral, name='create_referral'),
    path('payouts/setup/', views.onboard_cpa_stripe, name='onboard_cpa_stripe'),
    path('update-status/<int:pk>/', views.update_referral_status, name='update_referral_status'),
    path('profile/edit/', views.edit_profile, name='edit_profile'),
]
