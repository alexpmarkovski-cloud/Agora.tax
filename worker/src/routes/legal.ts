import { Hono } from 'hono';
import { renderLayout, renderLegalDoc } from '../layout';

// Ported from Customer/api/templates/api/legal_docs/*.html — these are plain
// TemplateViews in Django (Customer/api/urls.py:35-39), no context, no DB.
// Bundled with the landing-page slice since the shared footer links to them.
export const legalRoute = new Hono();

legalRoute.get('/terms-of-service/', (c) =>
  c.html(
    renderLayout(
      renderLegalDoc(
        'Terms of Service',
        [
          [
            '1. Acceptance of Terms',
            'By accessing or using the Agora.tax platform, you agree to be bound by these Terms of Service. If you disagree with any part of the terms, you may not access the service.',
          ],
          [
            '2. Description of Service',
            'Agora.tax provides a platform connecting Tax Professionals with Financial Institutions to facilitate secure and compliant client referrals.',
          ],
          [
            '3. Professional Obligations',
            'Users acting as Financial or Tax Professionals must maintain active, verifiable credentials (such as CRD or CPA licenses) to use the platform. Agora.tax reserves the right to suspend accounts failing verification.',
          ],
          [
            '4. Limitation of Liability',
            'Agora.tax acts strictly as a technology facilitator and is not a registered broker-dealer or financial advisor. We are not liable for the outcome of any financial services rendered by professionals on this platform.',
          ],
        ],
        'This is a placeholder document created for demonstration purposes. Agora.tax is currently a portfolio project and not an active commercial service.',
      ),
    ),
  ),
);

legalRoute.get('/privacy-policy/', (c) =>
  c.html(
    renderLayout(
      renderLegalDoc(
        'Privacy Policy',
        [
          [
            '1. Information We Collect',
            'We collect information you provide directly to us, including professional credentials, contact details, and client referral data required to facilitate connections.',
          ],
          [
            '2. How We Use Information',
            'Information is used strictly to operate the platform, verify professional standing, and process payouts securely through our payment partners (e.g., Stripe).',
          ],
          [
            '3. Information Sharing',
            'We share necessary client information with the specific Financial Institution selected during a referral. We do not sell your personal data to third parties.',
          ],
          [
            '4. Data Security',
            'We implement industry-standard security measures to protect your personal information and sensitive client data.',
          ],
        ],
        'This is a placeholder document created for demonstration purposes. Agora.tax is currently a portfolio project. No real user data is actively processed or sold.',
      ),
    ),
  ),
);

legalRoute.get('/platform-agreement/', (c) =>
  c.html(
    renderLayout(
      renderLegalDoc('Platform Agreement', [
        [
          '1. Professional Relationships',
          'This agreement governs the relationship between referring Professionals (e.g., CPAs) and receiving Financial Institutions. Agora.tax is an intermediary platform and is not a party to the independent engagements between referred clients and institutions.',
        ],
        [
          '2. Payouts and Fees',
          'Payouts for successful referrals are processed according to the terms specified on the individual Offer. Agora.tax automatically deducts a platform fee before routing payouts via Stripe. Professionals are responsible for their own taxes on any earnings.',
        ],
        [
          '3. Compliance',
          'All professionals agree to comply with relevant local, state, and federal regulations regarding client referrals, data privacy, and fiduciary duties.',
        ],
      ]),
    ),
  ),
);

legalRoute.get('/cookie-policy/', (c) =>
  c.html(
    renderLayout(
      renderLegalDoc('Cookie Policy', [
        [
          '1. What Are Cookies?',
          'Cookies are small text files stored on your device to enhance site navigation, analyze site usage, and assist in our authentication processes.',
        ],
        [
          '2. How We Use Cookies',
          'We use essential cookies strictly necessary to maintain your logged-in session securely and to prevent Cross-Site Request Forgery (CSRF) attacks.',
        ],
        [
          '3. Managing Cookies',
          'You can instruct your browser to refuse all cookies or to indicate when a cookie is being sent. However, refusing essential cookies will prevent you from logging into the platform.',
        ],
      ]),
    ),
  ),
);

legalRoute.get('/acceptable-use/', (c) =>
  c.html(
    renderLayout(
      renderLegalDoc('Acceptable Use Policy', [
        [
          '1. Prohibited Conduct',
          'Users may not use the Agora.tax platform to conduct fraudulent activities, misrepresent professional credentials, or spam financial institutions with unqualified referrals.',
        ],
        [
          '2. Data Scraping',
          'Automated scraping or extraction of platform data, including professional contact information or offer details, is strictly prohibited without explicit written consent.',
        ],
        [
          '3. Enforcement',
          'Violations of this policy may result in immediate account termination, forfeiture of pending payouts, and potential legal action depending on the severity of the violation.',
        ],
      ]),
    ),
  ),
);
