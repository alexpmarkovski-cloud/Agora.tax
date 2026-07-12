import re

with open('api/views.py', 'r') as f:
    content = f.read()

# 1. Imports
content = content.replace(' LegalCompany, LegalUser, LegalLicense, ', ' ')
content = content.replace(' LegalSignupForm, LegalLicenseForm, ', ' ')

# 2. edit_profile
content = re.sub(r"    legal_user = getattr\(request\.user, 'legal_user', None\)\n", "", content)
content = re.sub(r"            elif legal_user:\n                license_form = LegalLicenseForm\(request\.POST\)\n                if license_form\.is_valid\(\):\n                    license = license_form\.save\(commit=False\)\n                    license\.legal_user = legal_user\n                    license\.save\(\)\n                    return redirect\('edit_profile'\)\n", "", content)
content = re.sub(r"    elif legal_user:\n        license_form = LegalLicenseForm\(\)\n        licenses = legal_user\.licenses\.all\(\)\n", "", content)
content = content.replace(",\n        'legal_user': legal_user", "")

# 3. create_referral
content = re.sub(r"    legal_user = getattr\(request\.user, 'legal_user', None\)\n", "", content)
content = re.sub(r"    elif legal_user and legal_user\.licenses\.filter\(is_active=True\)\.exists\(\):\n        is_verified = True\n", "", content)
content = re.sub(r"            elif legal_user:\n                referral\.legal_user = legal_user\n", "", content)
content = re.sub(r"            elif legal_user:\n                return redirect\('legal_dashboard'\)\n", "", content)
content = content.replace("if cpa_user or legal_user or financial_user:", "if cpa_user or financial_user:")
content = content.replace("linked to a CPA, Legal, or Financial profile.", "linked to a CPA or Financial profile.")

# 4. pwm_state_selection
content = re.sub(r"    legal_user = getattr\(request\.user, 'legal_user', None\)\n", "", content)
content = content.replace("            legal_user=legal_user,\n", "")

# 5. login_redirect
content = re.sub(r"    elif hasattr\(request\.user, 'legal_user'\):\n        return redirect\('legal_dashboard'\)\n", "", content)

# 6. financial_user_required
content = content.replace(" and not hasattr(request.user, 'legal_user')", "")
content = content.replace("Financial or Legal Professionals", "Financial Professionals")

# 7. financial_dashboard
content = re.sub(r"    if hasattr\(request\.user, 'legal_user'\):\n        return redirect\('legal_dashboard'\)\n        \n", "", content)

# 8. create_offer
content = re.sub(r"    is_legal = hasattr\(request\.user, 'legal_user'\)\n    company = request\.user\.legal_user\.company if is_legal else request\.user\.financial_user\.company\n    dashboard_url = 'legal_dashboard' if is_legal else 'financial_dashboard'\n", "    company = request.user.financial_user.company\n    dashboard_url = 'financial_dashboard'\n", content)
content = content.replace("company=company if not is_legal else None,", "company=company,")
content = re.sub(r"                legal_company=company if is_legal else None\n", "", content)

# 9. create_product
content = re.sub(r"    is_legal = hasattr\(request\.user, 'legal_user'\)\n    company = request\.user\.legal_user\.company if is_legal else request\.user\.financial_user\.company\n    dashboard_url = 'legal_dashboard' if is_legal else 'financial_dashboard'\n", "    company = request.user.financial_user.company\n    dashboard_url = 'financial_dashboard'\n", content)
content = re.sub(r"            if is_legal:\n                product\.legal_company = company\n            else:\n                product\.company = company\n", "            product.company = company\n", content)

# 10. financial_referrals
content = re.sub(r"    is_legal = hasattr\(request\.user, 'legal_user'\)\n    company = request\.user\.legal_user\.company if is_legal else request\.user\.financial_user\.company\n    \n    if is_legal:\n        referrals = Referral\.objects\.filter\(offer__product__legal_company=company\)\.order_by\('-gen_date'\)\n    else:\n        referrals = Referral\.objects\.filter\(offer__product__company=company\)\.order_by\('-gen_date'\)\n", "    company = request.user.financial_user.company\n    referrals = Referral.objects.filter(offer__product__company=company).order_by('-gen_date')\n", content)

# 11. update_financial_pro_status
content = re.sub(r"    is_legal = hasattr\(request\.user, 'legal_user'\)\n    company = request\.user\.legal_user\.company if is_legal else request\.user\.financial_user\.company\n    \n    if is_legal:\n        referral = get_object_or_404\(Referral, pk=pk, offer__product__legal_company=company\)\n    else:\n        referral = get_object_or_404\(Referral, pk=pk, offer__product__company=company\)\n", "    company = request.user.financial_user.company\n    referral = get_object_or_404(Referral, pk=pk, offer__product__company=company)\n", content)

# 12. edit_offer
content = re.sub(r"    is_legal = hasattr\(request\.user, 'legal_user'\)\n    company = request\.user\.legal_user\.company if is_legal else request\.user\.financial_user\.company\n    dashboard_url = 'legal_dashboard' if is_legal else 'financial_dashboard'\n    offer = get_object_or_404\(Offer, pk=pk\)\n    \n    # Verify ownership\n    offer_company = offer\.product\.legal_company if is_legal else offer\.product\.company\n", "    company = request.user.financial_user.company\n    dashboard_url = 'financial_dashboard'\n    offer = get_object_or_404(Offer, pk=pk)\n    \n    # Verify ownership\n    offer_company = offer.product.company\n", content)
content = content.replace("                company=company if not is_legal else None,\n                legal_company=company if is_legal else None", "                company=company")

# 13. financial_update_referral
content = re.sub(r"    is_legal = hasattr\(request\.user, 'legal_user'\)\n    company = request\.user\.legal_user\.company if is_legal else request\.user\.financial_user\.company\n    dashboard_url = 'legal_dashboard' if is_legal else 'financial_dashboard'\n    referral = get_object_or_404\(Referral, pk=pk\)\n    \n    # Verify ownership\n    referral_company = referral\.offer\.product\.legal_company if is_legal else referral\.offer\.product\.company\n", "    company = request.user.financial_user.company\n    dashboard_url = 'financial_dashboard'\n    referral = get_object_or_404(Referral, pk=pk)\n    \n    # Verify ownership\n    referral_company = referral.offer.product.company\n", content)

# 14. Remove all Legal Professional Views at the end
content = re.sub(r"# ------------------ Legal Professional Views ------------------.*", "", content, flags=re.DOTALL)

with open('api/views.py', 'w') as f:
    f.write(content)

print("Modified views.py successfully.")
