// Shared page shell — ported from Customer/api/templates/api/shared/base.html.
//
// The nav is rendered logged-out for now. Once login/session lands (task: build
// login/session), this will take the current user/role and switch nav links the
// same way base.html does with {% if user.is_authenticated %}.

const currentYear = () => new Date().getUTCFullYear();

export function renderLayout(content: string): string {
  return `<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agora.tax Referral System</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet"
        integrity="sha384-9ndCyUaIbzAi2FUVXJi0CjmCapSmO7SnpJef0486qhLnuZ2cdeRhO02iuK6FUUVM" crossorigin="anonymous">
    <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.5/font/bootstrap-icons.css">
    <style>
        body { padding-top: 20px; }
    </style>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark mb-4 shadow-sm py-3" style="background-color: hsl(220, 45%, 12%) !important; border-bottom: 1px solid hsl(220, 30%, 20%);">
        <div class="container">
            <a class="navbar-brand fw-bold font-monospace d-flex align-items-center gap-2" href="/">
                <img src="/images/logo.png" alt="Agora.tax Logo" style="height: 36px; width: auto; border-radius: 6px; object-fit: contain;">
            </a>
            <button class="navbar-toggler border-0 shadow-none" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav"
                aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
                <span class="navbar-toggler-icon"></span>
            </button>
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto align-items-lg-center">
                    <li class="nav-item">
                        <a class="nav-link px-3" href="/contact/">Contact Support</a>
                    </li>
                </ul>
                <ul class="navbar-nav align-items-lg-center gap-1">
                    <li class="nav-item ms-lg-2">
                        <a class="btn btn-primary btn-sm px-4 fw-semibold rounded-pill" href="/login/"
                           style="background: linear-gradient(135deg, hsl(210, 100%, 60%) 0%, hsl(220, 100%, 50%) 100%); border: none;">
                           Partner Login
                        </a>
                    </li>
                </ul>
            </div>
        </div>
    </nav>
    <main class="container">
        ${content}
    </main>

    <footer class="bg-dark text-white-50 py-4 mt-5" style="border-top: 1px solid hsl(220, 30%, 20%); background-color: hsl(220, 45%, 12%) !important;">
        <div class="container text-center">
            <p class="mb-2">&copy; ${currentYear()} Agora.tax Demo Project</p>
            <ul class="list-inline mb-0">
                <li class="list-inline-item"><a href="/legal/terms-of-service/" class="text-white-50 text-decoration-none">Terms of Service</a></li>
                <li class="list-inline-item text-muted">|</li>
                <li class="list-inline-item"><a href="/legal/privacy-policy/" class="text-white-50 text-decoration-none">Privacy Policy</a></li>
                <li class="list-inline-item text-muted">|</li>
                <li class="list-inline-item"><a href="/legal/platform-agreement/" class="text-white-50 text-decoration-none">Platform Agreement</a></li>
                <li class="list-inline-item text-muted">|</li>
                <li class="list-inline-item"><a href="/legal/cookie-policy/" class="text-white-50 text-decoration-none">Cookie Policy</a></li>
                <li class="list-inline-item text-muted">|</li>
                <li class="list-inline-item"><a href="/legal/acceptable-use/" class="text-white-50 text-decoration-none">Acceptable Use Policy</a></li>
            </ul>
        </div>
    </footer>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/js/bootstrap.bundle.min.js"
        integrity="sha384-geWF76RCwLtnZ8qwWowPQNguL3RmwHVBC9FhGdlKrxdiJJigb/j/68SIy3Te4Bkz"
        crossorigin="anonymous"></script>
</body>
</html>`;
}

const DEFAULT_NOTICE =
  'This is a placeholder document created for demonstration purposes. Agora.tax is currently a portfolio project.';

export function renderLegalDoc(
  title: string,
  sections: [string, string][],
  notice: string = DEFAULT_NOTICE,
): string {
  const body = sections
    .map(([heading, text]) => `<h4>${heading}</h4>\n<p>${text}</p>`)
    .join('\n\n');

  return `<div class="container my-5">
    <div class="row justify-content-center">
        <div class="col-lg-8">
            <h1 class="mb-4 fw-bold">${title}</h1>
            <p class="text-muted mb-4">Last Updated: Today</p>

            <div class="alert alert-info">
                <strong>Notice:</strong> ${notice}
            </div>

            ${body}
        </div>
    </div>
</div>`;
}
