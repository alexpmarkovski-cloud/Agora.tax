import re

# Clean admin.py
with open('api/admin.py', 'r') as f:
    admin_content = f.read()

admin_content = admin_content.replace(' LegalCompany, LegalUser, LegalLicense, ', ' ')
admin_content = re.sub(r"@admin\.register\(LegalUser\)\nclass LegalUserAdmin\(admin\.ModelAdmin\):\n    list_display = \('user', 'company', 'created_at'\)\n    search_fields = \('user__username', 'user__email', 'company__name'\)\n\n", "", admin_content)
admin_content = re.sub(r"@admin\.register\(LegalCompany\)\nclass LegalCompanyAdmin\(admin\.ModelAdmin\):\n    list_display = \('name', 'integration_type', 'created_at'\)\n    search_fields = \('name',\)\n\n", "", admin_content)
admin_content = admin_content.replace("'legal_company', ", "")
admin_content = admin_content.replace("'legal_company__name', ", "")
admin_content = admin_content.replace("'legal_user', ", "")
admin_content = admin_content.replace("'legal_user__user__first_name', 'legal_user__user__last_name', ", "")

with open('api/admin.py', 'w') as f:
    f.write(admin_content)

# Clean forms.py
with open('api/forms.py', 'r') as f:
    forms_content = f.read()

forms_content = forms_content.replace(' LegalCompany, LegalUser, LegalLicense, ', ' ')
forms_content = re.sub(r"class LegalSignupForm\(forms\.ModelForm\):.*?(?=class FinancialLicenseForm)", "", forms_content, flags=re.DOTALL)
forms_content = re.sub(r"class LegalLicenseForm\(forms\.ModelForm\):.*?(?=\n\nclass FinancialLicenseForm)", "", forms_content, flags=re.DOTALL)

with open('api/forms.py', 'w') as f:
    f.write(forms_content)

print("Admin and forms cleaned")
