---
title: "Agora Django Architecture"
description: "The core architecture and structure of the Agora project."
---

# Agora Architecture Overview

The Agora project is a platform connecting CPAs with financial institutions. It is built using Django and follows standard architectural patterns.

## Core Stack
- **Framework**: Django 4.2.26
- **Language**: Python
- **Database**: 
  - **Local**: `db.sqlite3`
  - **Production**: PostgreSQL
- **Key Modules**:
  - `Customer/customer_db`: Main project configuration (settings, URLs).
  - `Customer/api`: Core application logic, models, and views.

## User Roles
- **CPA**: The primary platform users. They manage referrals for their clients.
- **Admin**: Staff users who manage the platform, verify CPAs, and approve payouts.
- **FinancialCompanyUser**: Users who work for the financial companies and can post offers to the platform.

## Core Domain Model
The system centers around the following key entities (found in `api/models.py`):
1. **FinancialCompany**: Providers like banks or investment firms.
2. **Product**: Financial offerings (e.g., "High Yield Savings").
3. **Offer**: Specific deals associated with products (e.g., "$300 Bonus").
4. **CPAUser**: Extended user profile for the CPAs.
5. **Referral**: Records of a client interacting with an offer.
6. **PayoutBatch**: Groups of referrals processed into payments.

## Integration Points
- **Bank Integrations**: Handled via API or manual processes.
- **Stripe**: Used for managing payouts to CPAs via Connect accounts.
- **Bank Account ID**: Managed via `settings.AGORA_MAIN_BANK_ID`.

## Security & Access
- Use built-in Django authentication exclusively.
- Financial transactions (payouts) are NEVER automated.
- All CPA-facing views require authentication.
- All admin views require administrative privileges.
