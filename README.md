# Pynotes Store — eCommerce Storefront

A production-ready, full-stack e-commerce storefront built with **Django 5 + Django REST Framework**,
server-rendered with **Tailwind CSS** and **Alpine.js**. It sells a demo catalog of Python/data-science
ebooks, courses, notebook bundles and developer merch, but the data model is generic enough to restock
with any product catalog.

> No design mockups or requirements were supplied for this project, so the UI/UX, catalog niche, and
> tech stack below were chosen deliberately (see "Design decisions" below) rather than copied from a
> reference — there was none to match.

## Features

- **Storefront**: home page, product listing with search/sort/filter, category pages, product detail
  pages with image gallery, star ratings and reviews, cart, multi-step checkout.
- **Accounts**: email-based signup/login/logout, password reset via email, profile editing, multiple
  shipping/billing addresses, order history.
- **Cart**: session-based for guests, merges into the user's cart on login, quantity updates, coupon
  codes.
- **Checkout & payments**: Stripe Checkout integration (card payments), webhook handler for reliable
  order confirmation, automatic stock decrement on payment, graceful **demo mode** that simulates a
  successful payment when no Stripe keys are configured (so the whole flow is testable out of the box).
- **Admin**: full Django admin for products, categories, images, reviews, coupons, orders (with status
  actions), users and addresses.
- **JSON API**: DRF-powered REST API under `/api/v1/` with JWT auth, product/category endpoints,
  cart endpoints, and the authenticated user's order history — for a future mobile app or SPA frontend.
- **Tests**: 50+ automated pytest tests covering models, views, cart logic, checkout/payment flow and
  the API.

## Tech stack

| Layer      | Choice                                                                 |
|------------|-------------------------------------------------------------------------|
| Backend    | Django 5.1, Django REST Framework, SimpleJWT                           |
| Database   | PostgreSQL in production, SQLite for local dev (auto-detected)         |
| Frontend   | Django templates, Tailwind CSS 3, Alpine.js (via CDN)                  |
| Payments   | Stripe Checkout + webhooks                                             |
| Static/media | WhiteNoise (static), local filesystem (media) — see "Deployment" for swapping in S3-style storage |
| Testing    | pytest, pytest-django, factory_boy                                     |
| Deployment | Docker + docker-compose, Gunicorn, GitHub Actions CI                   |

## Design decisions

This repository had no reference designs, mockups or product requirements attached to it. Rather than
guess at a business the user didn't specify, the following calls were made explicitly and can be revisited:

1. **Catalog niche** — "Pynotes": Python/data-science ebooks, video courses, notebook templates and
   developer merch. The model (`Category`, `Product`, `ProductImage`) is fully generic — swap the seed
   data in `apps/catalog/management/commands/seed_demo_data.py` for your own catalog.
2. **Visual design** — a clean, modern slate/blue storefront aesthetic (Tailwind), since there was no
   design system or brand guide to match.
3. **Backend stack** — Django (chosen over FastAPI) specifically to get a free, production-grade admin
   panel, built-in auth, and ORM/migrations, while DRF layers a JSON API on top for API-first needs.

## Project structure

```
config/                 # Django project (settings split into base/dev/test/prod, urls, wsgi/asgi)
apps/
  accounts/             # Custom email-based User model, addresses, auth views
  catalog/              # Categories, products, images, reviews, coupons + seed_demo_data command
  cart/                 # Session/DB-backed cart, middleware, services
  orders/                # Checkout, Order/OrderItem, Stripe integration, webhook
  core/                 # Home/about/contact pages, site-wide context processors
  api/                   # DRF serializers/viewsets/urls (/api/v1/)
templates/              # All HTML templates (base layout, partials, per-app pages)
static_src/input.css    # Tailwind source (compiled to static/css/output.css)
static/                 # Compiled CSS + JS, served by WhiteNoise
factories.py            # factory_boy test factories shared by all test modules
conftest.py             # pytest fixtures (DRF APIClient, etc.)
```

## Getting started (local development)

### Prerequisites
- Python 3.11+
- Node.js 18+ (only needed if you want to rebuild Tailwind CSS — the compiled CSS is already committed)

### Setup

```bash
git clone https://github.com/datanalytics90/Pynotes-eCommerce-Storefront.git
cd Pynotes-eCommerce-Storefront

python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements-dev.txt

cp .env.example .env
# Edit .env and set SECRET_KEY (see the command in .env.example), or leave the
# insecure dev default — it's fine for local use only.

python manage.py migrate
python manage.py seed_demo_data      # optional: populates demo products/categories/coupon
python manage.py createsuperuser

python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the storefront and `http://127.0.0.1:8000/admin/` for the admin panel.

### Rebuilding Tailwind CSS (optional)

Only needed if you change `static_src/input.css`, `tailwind.config.js`, or add new template classes:

```bash
npm install
npm run build:css      # one-off build
npm run watch:css      # rebuild on change, while developing
```

### Running tests

```bash
python -m pytest            # 51 tests, ~3s, uses an in-memory SQLite database
ruff check apps config      # lint
```

### Payments (Stripe)

If `STRIPE_SECRET_KEY` / `STRIPE_PUBLISHABLE_KEY` are **not** set, checkout runs in **demo mode**:
submitting the checkout form immediately marks the order as paid (clearly flagged to the user) so the
full purchase flow can be tested without any credentials.

To enable real Stripe Checkout (test mode):

1. Create a free account at https://dashboard.stripe.com and grab your **test** keys from
   https://dashboard.stripe.com/test/apikeys.
2. Set `STRIPE_PUBLISHABLE_KEY` and `STRIPE_SECRET_KEY` in `.env`.
3. For local webhook testing, install the [Stripe CLI](https://stripe.com/docs/stripe-cli) and run:
   ```bash
   stripe listen --forward-to localhost:8000/orders/webhook/stripe/
   ```
   Copy the printed `whsec_...` value into `STRIPE_WEBHOOK_SECRET`.
4. Test card number: `4242 4242 4242 4242`, any future expiry, any CVC.

## API

Base path: `/api/v1/`

| Endpoint                     | Method    | Auth        | Notes                                |
|-------------------------------|-----------|-------------|----------------------------------------|
| `/categories/`                | GET       | Public      | List active categories                |
| `/products/`                  | GET       | Public      | List/search/filter products           |
| `/products/{slug}/`           | GET       | Public      | Product detail                        |
| `/auth/register/`             | POST      | Public      | Create account                        |
| `/auth/token/`                | POST      | Public      | Obtain JWT access/refresh token pair  |
| `/auth/token/refresh/`        | POST      | Public      | Refresh an access token               |
| `/me/`                        | GET/PATCH | JWT/session | Current user profile                  |
| `/cart/`                      | GET/POST/DELETE | Public (session) | View/add/remove cart items     |
| `/orders/`                    | GET       | JWT/session | Authenticated user's own orders       |

## Deployment

### Option A — Docker (recommended, works anywhere)

```bash
cp .env.example .env   # fill in SECRET_KEY, ALLOWED_HOSTS, Stripe keys, etc.
docker compose up --build -d
docker compose exec web python manage.py createsuperuser
```

This runs Postgres + the Django app (Gunicorn) behind the `web` service, applying migrations
automatically on startup. Put a reverse proxy (nginx, Caddy, or your platform's built-in one) in front
of port 8000 for TLS termination in production.

### Option B — Render / Railway / Fly.io / Heroku-style platforms

1. Push this repo to GitHub (see below) and connect the repository to the platform.
2. Provision a managed PostgreSQL add-on and copy its connection string into `DATABASE_URL`.
3. Set environment variables from `.env.example` in the platform's dashboard — at minimum
   `SECRET_KEY`, `DEBUG=False`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`.
4. Build command: `pip install -r requirements.txt && npm install && npm run build:css && python manage.py collectstatic --noinput`
5. Release/migrate command: `python manage.py migrate`
6. Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
7. Set `DJANGO_SETTINGS_MODULE=config.settings.prod` in the platform's env vars (the `wsgi.py`/`asgi.py`
   entrypoints already default to `config.settings.prod`, so this is usually only needed if the platform
   overrides it).

### Environment variables reference

See [`.env.example`](.env.example) for the full list with comments. Required in production:
`SECRET_KEY`, `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`. Everything else has a safe
default or is optional (Stripe keys, email, CORS).

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: installs dependencies, builds Tailwind CSS,
lints with ruff, runs `manage.py check`, and runs the full pytest suite.

## Known limitations / next steps

- Media storage is local disk by default — swap `DEFAULT_FILE_STORAGE` for `django-storages` + S3 (or
  equivalent) before scaling past a single server, since local disk media won't survive redeploys on
  most PaaS platforms.
- Tax calculation is a flat `$0` placeholder (`tax_total` field exists on `Order` for future use) —
  wire up a real tax provider (Stripe Tax, TaxJar, etc.) before taking real orders.
- Shipping cost is a flat `$5` for any order containing physical goods — replace with real
  carrier-rate lookups if you ship physical products at scale.
- No Celery/async task queue — Stripe webhook processing and emails run synchronously, which is fine
  at small scale but worth revisiting under load.
