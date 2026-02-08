Agora Project Manifest (v1.0)
Status: Core Engine Complete | Database: PostgreSQL | Framework: Django

1. The Database Architecture (api/models.py)
We moved away from raw SQL to Django Models to enforce data integrity.

FinancialCompany: The "Whales" (Banks/Fintechs).

Product: specific items they sell (e.g., "High Yield Savings").

Offer: The contract terms (Price, Active Status, Dates).

CPAUser: The workforce (Links to Django's Auth User).

Referral: The core ledger.

Crucial Feature: Pricing Snapshots. We store agreed_cpa_payout and agreed_platform_fee directly on this table so historical data doesn't change if the Offer price changes later.

Transaction: (Placeholder) For future Stripe payments.

2. The Logic Layer (api/views.py)
We implemented three core functions to handle the workflow:

referral_list (The Dashboard)

Fetches referrals for the currently logged-in CPA.

Includes a "Safety Fallback" to grab the first user if testing without a linked profile.

Orders by gen_date (newest first).

create_referral (The Engine)

Auto-Detect Security: Automatically assigns the cpa_id based on the logged-in user (no dropdown menu for "Who are you?").

Pricing Lock: Looks up the Offer price and stamps it onto the Referral record instantly.

update_referral_status (The Action)

A secure POST request that flips a referral from PENDING → CONVERTED.

3. The Input Layer (api/forms.py)
We customized the standard Django form for security and usability:

Field Restriction: We strictly removed 'cpa', 'payout', and 'status' so users cannot fake their identity or price.

Smart Filtering (__init__): The "Offer" dropdown only shows offers where is_active=True.

4. The Interface (Templates)
We moved to a "Base Layout" architecture to avoid repeating code.

base.html: The master layout containing the Navbar (Login/Logout, Dashboard links) and Bootstrap 5 styling.

registration/login.html: The standard Django login interface.

api/create_referral.html: The styled form for data entry.

api/referral_list.html: The main dashboard table with status badges and the "Mark Converted" button.

5. The Control Center (api/admin.py)
We upgraded the default Admin Panel to a "Pro" Dashboard:

Search Bars: Added to find specific referrals or users.

Filters: Sidebar filters for status, company, and date.

List Displays: Columns show meaningful data (e.g., Price, Email) instead of just "Object #1".

6. Configuration & Security
settings.py:

Configured LOGIN_REDIRECT_URL to send users straight to their dashboard.

Enabled django.contrib.auth.

urls.py:

Mapped api/ endpoints.

Mapped accounts/ for the login system.

.gitignore: Added venv, .env, and __pycache__ to keep the repo clean.