---
title: "Django Development Patterns"
description: "Best practices and common patterns for developing in the OG Agora Django environment."
---

# Django Development Patterns

Follow these guidelines for consistent development within the OG Agora project.

## Authentication & Users
- **Custom Model**: Always use the `CPAUser` model for CPA-related functionality. It is linked to the standard Django `User` via a `OneToOneField`.
- **Registration**: Signup is handled via `django-allauth` with a custom `CPASignupForm` found in `api/forms.py`.
- **Redirects**:
  - `LOGIN_REDIRECT_URL = 'referral_list'`
  - `LOGOUT_REDIRECT_URL = 'login'`

## Permissions & Views
- **Access Control**: Use Django's built-in decorators and mixins for access control.
- **CPA-Facing Views**: All views intended for CPAs MUST be protected by `@login_required`.
- **Administrative Views**: All admin-only views MUST require BOTH `@login_required` AND a custom `@is_admin` decorator (ensure you check for staff/superuser status).

## Financial Integrity
> [!IMPORTANT]
> **Financial Security**: Never implement automated payouts. All payouts MUST require manual review and approval by an administrator.

### Stripe Integration
- Use the provided environment variables: `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY`.
- Follow the patterns in `PayoutBatch` for processing conversions into payouts.

## Templates
- Keep styles centralized where possible, but use the `templates/api` and `templates/registration` directories for UI components.
- Ensure all forms use `{% csrf_token %}`.
