from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User
from api.models import FinancialCompany, ProductCategory, Product, Offer, CPAUser, Referral, FinancialUser, LegalCompany, LegalUser, LegalLicense, FinancialLicense
from api.forms import ReferralForm

class FinancialPortalTests(TestCase):
    def setUp(self):
        # Set up financial companies
        self.company1 = FinancialCompany.objects.create(name="Apex Bank", integration_type="API")
        self.company2 = FinancialCompany.objects.create(name="Sovereign Trust", integration_type="MANUAL")

        # Set up product categories
        self.cat_hys = ProductCategory.objects.create(name="High-Yield Savings", client_type="Individual")
        
        # Set up products
        self.product1 = Product.objects.create(company=self.company1, category=self.cat_hys, name="Apex Platinum HYS")
        self.product2 = Product.objects.create(company=self.company2, category=self.cat_hys, name="Sovereign Gold HYS")

        # Set up offers
        self.offer1 = Offer.objects.create(
            product=self.product1,
            name="Apex Savings Promo",
            cpa_payout=250.00,
            platform_fee=100.00,
            client_bonus_summary="$300 Bonus",
            is_active=True
        )
        self.offer2 = Offer.objects.create(
            product=self.product2,
            name="Sovereign Savings Promo",
            cpa_payout=300.00,
            platform_fee=150.00,
            client_bonus_summary="$350 Bonus",
            is_active=True
        )

        # Set up users & profiles
        self.cpa_user_auth = User.objects.create_user(username="cpa_john", email="john@example.com", password="password123")
        self.cpa_profile = CPAUser.objects.create(
            user=self.cpa_user_auth,
            first_name="John",
            last_name="Doe",
            email="john@example.com",
            company_name="John Doe CPA LLC"
        )

        self.fin_user_auth1 = User.objects.create_user(username="apex_banker", email="banker1@apex.com", password="password123")
        self.fin_profile1 = FinancialUser.objects.create(
            user=self.fin_user_auth1,
            company=self.company1
        )

        self.fin_user_auth2 = User.objects.create_user(username="sov_banker", email="banker2@sov.com", password="password123")
        self.fin_profile2 = FinancialUser.objects.create(
            user=self.fin_user_auth2,
            company=self.company2
        )

        self.staff_user = User.objects.create_superuser(username="admin", email="admin@agora.com", password="password123")

        # Create sample referrals
        self.referral1 = Referral.objects.create(
            cpa=self.cpa_profile,
            offer=self.offer1,
            client_name="Client One",
            client_email="client1@example.com",
            client_phone="(555) 019-2834",
            status="PENDING",
            agreed_cpa_payout=250.00,
            agreed_platform_fee=100.00
        )
        self.referral2 = Referral.objects.create(
            cpa=self.cpa_profile,
            offer=self.offer2,
            client_name="Client Two",
            client_email="client2@example.com",
            client_phone="(555) 019-5678",
            status="PENDING",
            agreed_cpa_payout=300.00,
            agreed_platform_fee=150.00
        )



    def test_unauthenticated_redirects(self):
        """Verify unauthenticated users cannot access financial views."""
        urls = [
            reverse('financial_dashboard'),
            reverse('create_offer'),
            reverse('edit_offer', kwargs={'pk': self.offer1.pk}),
            reverse('financial_update_referral', kwargs={'pk': self.referral1.pk})
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertIn('/accounts/login/', response.url)

    def test_cpa_user_forbidden(self):
        """Verify a CPA user is redirected away from financial pages."""
        self.client.login(username="cpa_john", password="password123")
        urls = [
            reverse('financial_dashboard'),
            reverse('create_offer'),
            reverse('edit_offer', kwargs={'pk': self.offer1.pk}),
            reverse('financial_update_referral', kwargs={'pk': self.referral1.pk})
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(response.url, reverse('landing_page'))

    def test_login_redirect_routing(self):
        """Verify login_redirect correctly routes users based on their role."""
        # Staff routing
        self.client.login(username="admin", password="password123")
        response = self.client.get(reverse('login_redirect'))
        self.assertRedirects(response, reverse('referral_list'))
        self.client.logout()

        # Financial routing
        self.client.login(username="apex_banker", password="password123")
        response = self.client.get(reverse('login_redirect'))
        self.assertRedirects(response, reverse('financial_dashboard'))
        self.client.logout()

        # CPA routing
        self.client.login(username="cpa_john", password="password123")
        response = self.client.get(reverse('login_redirect'))
        self.assertRedirects(response, reverse('cpa_dashboard'))

    def test_financial_signup(self):
        """Verify that registering a new financial employee works."""
        response = self.client.post(reverse('financial_signup'), {
            'username': 'new_banker',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@apex.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'company': self.company1.id,
            'crd_number': 'CRD-12345',
            'state_registered': 'NY',
            'crd_active': True
        })
        self.assertRedirects(response, reverse('financial_dashboard'))
        
        # Verify database objects created
        user = User.objects.get(username="new_banker")
        self.assertEqual(user.first_name, "Jane")
        self.assertEqual(user.last_name, "Smith")
        self.assertEqual(user.email, "jane@apex.com")
        self.assertTrue(hasattr(user, 'financial_user'))
        self.assertEqual(user.financial_user.company, self.company1)
        
        # Verify license created
        licenses = user.financial_user.licenses.all()
        self.assertEqual(licenses.count(), 1)
        self.assertEqual(licenses[0].crd_number, 'CRD-12345')
        self.assertEqual(licenses[0].state, 'NY')
        self.assertTrue(licenses[0].is_active)

    def test_financial_add_license_via_profile(self):
        """Verify a financial professional can add another state CRD license in their profile settings."""
        # Authenticate fin_user_auth1
        self.client.login(username="apex_banker", password="password123")
        
        # Verify initial license count is 0 for fin_profile1
        self.assertEqual(self.fin_profile1.licenses.count(), 0)
        
        # Post a new license to edit_profile view
        response = self.client.post(reverse('edit_profile'), {
            'add_license': '',
            'state': 'CA',
            'crd_number': 'CRD-54321',
            'is_active': True
        })
        self.assertRedirects(response, reverse('edit_profile'))
        
        # Verify database has the new license
        licenses = self.fin_profile1.licenses.all()
        self.assertEqual(licenses.count(), 1)
        self.assertEqual(licenses[0].state, 'CA')
        self.assertEqual(licenses[0].crd_number, 'CRD-54321')
        self.assertTrue(licenses[0].is_active)

    def test_financial_dashboard_isolation(self):
        """Verify financial dashboard only shows the logged-in company's details."""
        self.client.login(username="apex_banker", password="password123")
        response = self.client.get(reverse('financial_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Should show Apex Bank offers and referrals
        self.assertContains(response, "Apex Bank")
        self.assertContains(response, "Apex Savings Promo")
        self.assertContains(response, "client1@example.com")
        self.assertContains(response, "Client One")
        self.assertContains(response, "(555) 019-2834")

        # Should NOT show Sovereign Trust details
        self.assertNotContains(response, "Sovereign Trust")
        self.assertNotContains(response, "Sovereign Savings Promo")
        self.assertNotContains(response, "client2@example.com")
        self.assertNotContains(response, "Client Two")
        self.assertNotContains(response, "(555) 019-5678")

    def test_financial_dashboard_metrics(self):
        """Verify metrics calculations are correct."""
        # Setup one converted referral to check metrics
        self.referral1.status = 'CONVERTED'
        self.referral1.save()
        
        # Add another pending referral to company 1
        Referral.objects.create(
            cpa=self.cpa_profile,
            offer=self.offer1,
            client_email="client3@example.com",
            status="PENDING",
            agreed_cpa_payout=250.00,
            agreed_platform_fee=100.00
        )


        self.client.login(username="apex_banker", password="password123")
        response = self.client.get(reverse('financial_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # 2 total leads, 1 converted lead, 50.0% conversion rate
        self.assertEqual(response.context['converted_count'], 1)
        self.assertEqual(response.context['conversion_rate'], 50.0)

    def test_create_offer_success(self):
        """Verify financial users can create offers."""
        self.client.login(username="apex_banker", password="password123")
        
        # Attempt to create an offer
        response = self.client.post(reverse('create_offer'), {
            'category': self.cat_hys.id,
            'name': 'Apex Q3 Super Saver',
            'client_bonus_summary': '$200 Cash Bonus',
            'client_requirements': 'Requirements go here',
            'is_active': True
        })
        self.assertRedirects(response, reverse('financial_dashboard'))
        self.assertTrue(Offer.objects.filter(name='Apex Q3 Super Saver').exists())

    def test_edit_offer_ownership(self):
        """Verify financial users cannot edit other companies' offers."""
        self.client.login(username="apex_banker", password="password123")
        
        # Edit own offer
        response = self.client.post(reverse('edit_offer', kwargs={'pk': self.offer1.pk}), {
            'category': self.cat_hys.id,
            'name': 'Apex Savings Promo Edited',
            'client_bonus_summary': '$320 Bonus',
            'client_requirements': 'Requirements updated',
            'is_active': True
        })
        self.assertRedirects(response, reverse('financial_dashboard'))
        self.offer1.refresh_from_db()
        self.assertEqual(self.offer1.name, 'Apex Savings Promo Edited')

        # Edit other company's offer should redirect and show error
        response = self.client.post(reverse('edit_offer', kwargs={'pk': self.offer2.pk}), {
            'category': self.cat_hys.id,
            'name': 'Rogue Sovereign Promo',
            'client_bonus_summary': '$350 Bonus',
            'client_requirements': 'Requirements updated',
            'is_active': True
        })
        self.assertRedirects(response, reverse('financial_dashboard'))
        self.offer2.refresh_from_db()
        self.assertNotEqual(self.offer2.name, 'Rogue Sovereign Promo')

    def test_update_referral_state(self):
        """Verify financial users can convert/reject own referrals, but not others."""
        self.client.login(username="apex_banker", password="password123")

        # Approve own referral
        response = self.client.post(reverse('financial_update_referral', kwargs={'pk': self.referral1.pk}), {
            'action': 'approve'
        })
        self.assertRedirects(response, reverse('financial_dashboard'))
        self.referral1.refresh_from_db()
        self.assertEqual(self.referral1.status, 'CONVERTED')

        # Approve other company's referral should be denied
        response = self.client.post(reverse('financial_update_referral', kwargs={'pk': self.referral2.pk}), {
            'action': 'approve'
        })
        self.assertRedirects(response, reverse('financial_dashboard'))
        self.referral2.refresh_from_db()
        self.assertEqual(self.referral2.status, 'PENDING')

    def test_referral_form_validations(self):
        """Verify the new ReferralForm validation rules (required fields, consent, email/phone)."""
        # 1. Successful form validation (only email provided)
        form_data = {
            'client_name': 'Jane Doe',
            'client_type': 'Individual',
            'category': 'High-Yield Savings',
            'offer': self.offer1.id,
            'client_email': 'jane@example.com',
            'client_phone': '',
            'consent': True
        }
        form = ReferralForm(data=form_data)
        self.assertTrue(form.is_valid())

        # 2. Successful form validation (only phone provided)
        form_data = {
            'client_name': 'Jane Doe',
            'client_type': 'Individual',
            'category': 'High-Yield Savings',
            'offer': self.offer1.id,
            'client_email': '',
            'client_phone': '555-1234',
            'consent': True
        }
        form = ReferralForm(data=form_data)
        self.assertTrue(form.is_valid())

        # 3. Missing both email and phone should fail validation
        form_data = {
            'client_name': 'Jane Doe',
            'client_type': 'Individual',
            'category': 'High-Yield Savings',
            'offer': self.offer1.id,
            'client_email': '',
            'client_phone': '',
            'consent': True
        }
        form = ReferralForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("__all__", form.errors) # raised as non_field_error in clean()
        self.assertIn("at least one contact method", form.errors["__all__"][0])

        # 4. Missing consent checkbox should fail validation
        form_data = {
            'client_name': 'Jane Doe',
            'client_type': 'Individual',
            'category': 'High-Yield Savings',
            'offer': self.offer1.id,
            'client_email': 'jane@example.com',
            'client_phone': '',
            'consent': False
        }
        form = ReferralForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("consent", form.errors)

        # 5. Missing client_name, client_type, or category should fail validation
        form_data = {
            'client_name': '',
            'client_type': '',
            'category': '',
            'offer': self.offer1.id,
            'client_email': 'jane@example.com',
            'client_phone': '',
            'consent': True
        }
        form = ReferralForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn("client_name", form.errors)
        self.assertIn("client_type", form.errors)
        self.assertIn("category", form.errors)

    def test_create_referral_as_financial_user(self):
        """Verify that a financial user can successfully create a referral."""
        self.client.login(username="apex_banker", password="password123")
        response = self.client.post(reverse('create_referral'), {
            'client_name': 'Jane Doe',
            'client_type': 'Individual',
            'category': 'High-Yield Savings',
            'offer': self.offer1.id,
            'client_email': 'jane@example.com',
            'client_phone': '',
            'consent': True
        })
        self.assertRedirects(response, reverse('financial_dashboard'))
        
        # Verify database objects created
        referral = Referral.objects.filter(client_name='Jane Doe').first()
        self.assertIsNotNone(referral)
        self.assertEqual(referral.financial_user, self.fin_profile1)
        self.assertEqual(referral.offer, self.offer1)

    def test_financial_dashboard_with_made_referrals(self):
        """Verify that the financial dashboard correctly displays received and made referrals."""
        # Create a referral made by self.fin_profile1
        made_ref = Referral.objects.create(
            financial_user=self.fin_profile1,
            offer=self.offer2, # referral made to Sovereign Trust offer
            client_name="Client Made",
            client_email="clientmade@example.com",
            client_phone="(555) 019-9999",
            status="PENDING",
            agreed_cpa_payout=300.00,
            agreed_platform_fee=150.00
        )
        
        # Create an incoming referral (received by Apex Bank, i.e., offer1)
        incoming_ref = Referral.objects.create(
            cpa=self.cpa_profile,
            offer=self.offer1,
            client_name="Client Incoming",
            client_email="incoming@example.com",
            client_phone="(555) 019-1111",
            status="PENDING",
            agreed_cpa_payout=250.00,
            agreed_platform_fee=100.00
        )
        
        self.client.login(username="apex_banker", password="password123")
        response = self.client.get(reverse('financial_dashboard'))
        self.assertEqual(response.status_code, 200)
        
        # Verify received referrals in context (i.e. 'referrals')
        referrals = response.context['referrals']
        self.assertIn(incoming_ref, referrals)
        self.assertNotIn(made_ref, referrals)
        
        # Verify made referrals in context (i.e. 'referrals_made')
        referrals_made = response.context['referrals_made']
        self.assertIn(made_ref, referrals_made)
        self.assertNotIn(incoming_ref, referrals_made)


class LegalPortalTests(TestCase):
    def setUp(self):
        # Set up a category
        self.cat_legal = ProductCategory.objects.create(name="Business Structuring", client_type="Business")
        # Set up a legal company
        self.legal_company = LegalCompany.objects.create(name="Lex & Partners", integration_type="MANUAL")
        
        # Set up a legal user
        self.legal_user_auth = User.objects.create_user(username="legal_jane", email="jane@lex.com", password="password123")
        self.legal_profile = LegalUser.objects.create(
            user=self.legal_user_auth,
            company=self.legal_company
        )
        self.license = LegalLicense.objects.create(
            legal_user=self.legal_profile,
            state="NY",
            bar_number="BAR12345",
            is_active=True
        )

        # Set up a financial company and offer to refer to
        self.fin_company = FinancialCompany.objects.create(name="Central Bank", integration_type="API")
        self.fin_category = ProductCategory.objects.create(name="Savings Account", client_type="Individual")
        self.product = Product.objects.create(company=self.fin_company, category=self.fin_category, name="HY Savings")
        self.offer = Offer.objects.create(
            product=self.product,
            name="Apex Promo",
            cpa_payout=200.00,
            platform_fee=50.00,
            is_active=True
        )

    def test_legal_signup(self):
        """Verify registering a new legal professional works."""
        response = self.client.post(reverse('legal_signup'), {
            'username': 'legal_bob',
            'first_name': 'Bob',
            'last_name': 'Vance',
            'email': 'bob@vance.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'new_company_name': 'Vance Legal Services',
            'bar_number': 'BAR67890',
            'state_registered': 'TX',
            'bar_active': True
        })
        self.assertRedirects(response, reverse('legal_dashboard'))
        
        # Verify db objects
        user = User.objects.get(username="legal_bob")
        self.assertEqual(user.first_name, "Bob")
        self.assertEqual(user.last_name, "Vance")
        self.assertTrue(hasattr(user, 'legal_user'))
        self.assertEqual(user.legal_user.company.name, 'Vance Legal Services')
        self.assertEqual(user.legal_user.licenses.first().bar_number, 'BAR67890')
        self.assertEqual(user.legal_user.licenses.first().state, 'TX')

    def test_legal_login(self):
        """Verify custom legal login page and role check works."""
        # Non-legal user login on legal page should fail
        cpa_auth = User.objects.create_user(username="some_cpa", password="password123")
        response = self.client.post(reverse('legal_login'), {
            'username': 'some_cpa',
            'password': 'password123'
        })
        self.assertEqual(response.status_code, 200) # Re-rendered form
        self.assertContains(response, "This portal is for Legal Professionals only")

        # Legal user login on legal page should succeed
        response = self.client.post(reverse('legal_login'), {
            'username': 'legal_jane',
            'password': 'password123'
        })
        self.assertRedirects(response, reverse('legal_dashboard'))

    def test_create_referral_as_legal_user(self):
        """Verify legal professional can recommend a client."""
        self.client.login(username="legal_jane", password="password123")
        response = self.client.post(reverse('create_referral'), {
            'client_name': 'Acme Corp',
            'client_type': 'Individual',
            'category': 'Savings Account',
            'offer': self.offer.id,
            'client_email': 'acme@example.com',
            'consent': True
        })
        self.assertRedirects(response, reverse('legal_dashboard'))
        
        # Verify referral
        ref = Referral.objects.get(client_name="Acme Corp")
        self.assertEqual(ref.legal_user, self.legal_profile)
        self.assertIsNone(ref.cpa)

    def test_create_offer_as_legal_user(self):
        """Verify legal professional can create an offer for their firm."""
        self.client.login(username="legal_jane", password="password123")
        response = self.client.post(reverse('create_offer'), {
            'category': self.cat_legal.id,
            'name': 'Corporate Setup Special',
            'client_bonus_summary': 'Free incorporation filing',
            'client_requirements': 'Requirements',
            'is_active': True
        })
        self.assertRedirects(response, reverse('legal_dashboard'))
        self.assertTrue(Offer.objects.filter(name='Corporate Setup Special').exists())
        
        # Verify product is linked to legal_company
        prod = Product.objects.get(name="Business Structuring")
        self.assertEqual(prod.legal_company, self.legal_company)
        self.assertIsNone(prod.company)


from api.forms import CPASignupForm, ContactInquiryForm, FinancialSignupForm, LegalSignupForm

class HoneypotSpamProtectionTests(TestCase):
    def test_cpa_signup_honeypot_triggered(self):
        """Verify CPA signup form fails if honeypot field is filled."""
        form = CPASignupForm(data={
            'first_name': 'John',
            'last_name': 'Doe',
            'company_name': 'Doe CPA',
            'license_number': '12345',
            'license_state': 'NY',
            'website': 'http://spambot.com'  # Honeypot filled
        })
        self.assertFalse(form.is_valid())
        self.assertIn('website', form.errors)
        self.assertIn('Anti-spam protection', form.errors['website'][0])

    def test_contact_support_honeypot_triggered(self):
        """Verify contact support form fails if honeypot field is filled."""
        form = ContactInquiryForm(data={
            'inquiry_type': 'General Support',
            'notes': 'Test notes',
            'website': 'http://spambot.com'  # Honeypot filled
        })
        self.assertFalse(form.is_valid())
        self.assertIn('website', form.errors)
        self.assertIn('Anti-spam protection', form.errors['website'][0])

    def test_financial_signup_honeypot_triggered(self):
        """Verify financial signup form fails if honeypot field is filled."""
        form = FinancialSignupForm(data={
            'username': 'new_banker',
            'first_name': 'Jane',
            'last_name': 'Smith',
            'email': 'jane@apex.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'new_company_name': 'New Institution',
            'website': 'http://spambot.com'  # Honeypot filled
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Anti-spam protection', form.errors['__all__'][0])

    def test_legal_signup_honeypot_triggered(self):
        """Verify legal signup form fails if honeypot field is filled."""
        form = LegalSignupForm(data={
            'username': 'legal_bob',
            'first_name': 'Bob',
            'last_name': 'Vance',
            'email': 'bob@vance.com',
            'password': 'securepassword123',
            'password_confirm': 'securepassword123',
            'new_company_name': 'Vance Legal',
            'bar_number': 'BAR67890',
            'state_registered': 'TX',
            'bar_active': True,
            'website': 'http://spambot.com'  # Honeypot filled
        })
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('Anti-spam protection', form.errors['__all__'][0])

