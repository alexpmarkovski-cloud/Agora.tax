import { Hono } from 'hono';
import { renderLayout } from '../layout';
import type { Env } from '../env';

// Ported from Customer/api/views.py:339-340 (landing_page) and
// Customer/api/templates/api/shared/landing_page.html. No DB, no auth —
// first slice, just proving the Worker itself runs and renders.
export const landingRoute = new Hono<{ Bindings: Env }>();

landingRoute.get('/', (c) => {
  // CPA signup stays on Django/allauth permanently (see plan), so this link
  // crosses apps rather than pointing at a Worker route.
  const cpaSignupUrl = `${c.env.DJANGO_APP_BASE_URL}/accounts/signup/?next=/my-referrals/`;

  const content = `
    <style>
        .hero-section {
            background: linear-gradient(135deg, hsl(220, 45%, 12%) 0%, hsl(220, 30%, 20%) 100%);
            color: white;
            padding: 5rem 0;
            border-radius: 12px;
            margin-bottom: 3rem;
            text-align: center;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
        }
        .hero-section h1 { font-weight: 800; font-size: 3rem; margin-bottom: 1.5rem; }
        .hero-section p.lead { font-size: 1.25rem; opacity: 0.9; max-width: 700px; margin: 0 auto 2.5rem; }
        .cta-container { display: flex; gap: 1.5rem; justify-content: center; flex-wrap: wrap; }
        .btn-primary-cta {
            background: linear-gradient(135deg, hsl(210, 100%, 60%) 0%, hsl(220, 100%, 50%) 100%);
            color: white; border: none; padding: 1rem 2.5rem; font-size: 1.1rem; font-weight: 600;
            border-radius: 50px; transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn-primary-cta:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 123, 255, 0.3); color: white; }
        .btn-secondary-cta {
            background: transparent; color: white; border: 2px solid rgba(255, 255, 255, 0.8);
            padding: 1rem 2.5rem; font-size: 1.1rem; font-weight: 600; border-radius: 50px; transition: all 0.2s;
        }
        .btn-secondary-cta:hover { background: rgba(255, 255, 255, 0.1); color: white; border-color: white; transform: translateY(-2px); }
        .how-it-works { padding: 3rem 0; }
        .how-it-works h2 { font-weight: 700; text-align: center; margin-bottom: 3rem; }
        .step-card {
            background: white; border-radius: 12px; padding: 2rem; text-align: center;
            box-shadow: 0 4px 15px rgba(0,0,0,0.05); height: 100%; border: 1px solid rgba(0,0,0,0.05);
        }
        .step-icon { font-size: 2.5rem; color: hsl(210, 100%, 60%); margin-bottom: 1.5rem; }
        .step-title { font-weight: 700; margin-bottom: 1rem; }
    </style>

    <div class="hero-section">
        <div class="container">
            <h1>Connect Your Clients with Trusted Financial Products</h1>
            <p class="lead">Agora.tax bridges the gap between Tax Professionals and Financial Institutions, creating a seamless referral ecosystem that benefits everyone.</p>

            <div class="cta-container mb-3">
                <a href="${cpaSignupUrl}" class="btn-primary-cta">CPA Registration</a>
                <a href="/financial/signup/" class="btn-secondary-cta">Financial Pros Registration</a>
            </div>
            <div class="mt-4">
                <span class="text-white-50 me-2">Already have an account?</span>
                <a href="/login/" class="text-white fw-bold text-decoration-none border-bottom border-white pb-1">Partner Login</a>
            </div>
        </div>
    </div>

    <div class="container how-it-works">
        <h2>How the Ecosystem Works</h2>
        <div class="row g-4">
            <div class="col-md-4">
                <div class="step-card">
                    <div class="step-icon"><i class="bi bi-person-lines-fill"></i></div>
                    <h3 class="step-title">1. Identify Needs</h3>
                    <p class="text-muted">As a CPA, you identify areas where your clients could benefit from specific financial products, for individuals and businesses.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="step-card">
                    <div class="step-icon"><i class="bi bi-arrow-left-right"></i></div>
                    <h3 class="step-title">2. Secure Referral</h3>
                    <p class="text-muted">With explicit consent, securely refer your client to top-tier financial institutions through the Agora platform.</p>
                </div>
            </div>
            <div class="col-md-4">
                <div class="step-card">
                    <div class="step-icon"><i class="bi bi-graph-up-arrow"></i></div>
                    <h3 class="step-title">3. Expert Fulfillment</h3>
                    <p class="text-muted">Financial Professionals receive the referral instantly and contact the client directly to provide the perfect financial solution.</p>
                </div>
            </div>
        </div>
    </div>
  `;

  return c.html(renderLayout(content));
});
