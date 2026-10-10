# PyNotes — Printed Coding Notes Storefront

A production-ready e-commerce storefront for **PyNotes**, a store selling printed,
handwritten-style coding notes (Python, Java, C, C++, DSA and more) across India. Built with
**Django 5 + Django REST Framework**, rendered with the supplied **Bootstrap 5** frontend and
brand kit, with **Razorpay** (prepaid) + **Cash on Delivery** checkout, **Smart Bundles** whose
stock is derived from their component books, GST invoicing, and Shiprocket-style order tracking.

This implementation follows the four spec documents supplied with the project
(`Pynotes-1-Functionality-and-Plugin-List.pdf`, `-2-System-Architecture-Flow-Chart.pdf`,
`-3-MySQL-Database-Architecture.pdf`, `-4-Backend-Architecture.pdf`) and the `PyNotes_Brand_Guideline.pdf`
and supplied Bootstrap HTML frontend — but rebuilt on Django instead of WordPress/WooCommerce, since
those documents describe the *target functionality*, not a prescribed tech stack.

## Features

- **Storefront**: home, catalogue with search/sort/category filters (including DSA → DSA with
  Python / DSA with Java sub-categories), product detail pages with gallery, star ratings and
  reviews, Smart Bundles (stock computed live from their books), a slide-out cart drawer, "Buy It
  Now", and the exact brand visual design (Nunito/Montserrat, Navy/Teal/Mint palette, animations).
- **Checkout**: guest or account checkout, **Prepaid** (Razorpay: UPI/cards/wallets, with an
  automatic admin-configurable discount) or **Cash on Delivery** (with an admin-configurable fee),
  free shipping, coupon codes.
- **Orders**: full status lifecycle (Pending payment → Processing → Shipped → Delivered, plus
  On hold/Cancelled/Refunded/Failed), COD phone/WhatsApp confirmation workflow, Shiprocket-style
  courier/AWB/tracking-link fields, a guest-accessible order tracking page, a 48-hour "report an
  issue" flow for damaged/wrong items, and downloadable **GST invoices** (PDF).
- **Admin**: Django admin for products/bundles/categories/orders/coupons/testimonials/FAQs/legal
  pages/site settings, plus **Shop Manager** and **Editor** permission groups matching the spec's
  role breakdown (`python manage.py setup_roles`).
- **Content**: an editable "Site Settings" singleton (prepaid discount %, COD fee, GSTIN,
  WhatsApp number, delivery notes), a repeater-style announcement bar, testimonials, FAQs grouped
  by topic, and editable legal pages (Privacy/Terms/Shipping/Refund) — the Django-admin equivalent
  of the spec's SCF options pages.
- **JSON API**: DRF-powered REST API under `/api/v1/` with JWT auth, for a future mobile app.
- **Tests**: 76 automated pytest tests covering models (including bundle stock math), views, the
  full COD and prepaid-demo-mode checkout flows, GST invoice generation, and the API.

## Tech stack

| Layer      | Choice                                                                   |
|------------|---------------------------------------------------------------------------|
| Backend    | Django 5.1, Django REST Framework, SimpleJWT                             |
| Database   | PostgreSQL in production, SQLite for local dev (auto-detected)           |
| Frontend   | The supplied Bootstrap 5 HTML/CSS/JS, served as Django templates/static  |
| Payments   | Razorpay (Orders API + Checkout.js) for prepaid, native COD flow          |
| Invoicing  | reportlab-generated GST invoice PDFs                                     |
| Testing    | pytest, pytest-django, factory_boy                                       |
| Deployment | Docker + docker-compose, Gunicorn, GitHub Actions CI                      |

## Project structure

```
config/                 # Django project (settings split into base/dev/test/prod)
apps/
  accounts/             # Custom email-based User model, addresses, auth, dashboard
  catalog/              # Category (with parent/child), Product, BundleItem, Review, Coupon
                         #   + seed_demo_data command (13 books, 4 bundles, FAQs, legal pages...)
  cart/                 # Session/DB-backed cart, middleware, services, Buy-It-Now
  orders/               # Checkout, Razorpay + COD, GST invoice PDF, tracking, issue reports
  core/                 # Home/about/contact/FAQ/legal pages, SiteSettings, Testimonial, FAQ
                         #   + setup_roles command (Shop Manager / Editor groups)
  api/                  # DRF serializers/viewsets/urls (/api/v1/)
templates/              # HTML templates — ported from the supplied Bootstrap frontend
static/                 # The supplied style.css/main.js/logo assets, used as-is
factories.py            # factory_boy test factories shared by all test modules
```

## Getting started (local development)

### Prerequisites
- Python 3.11+

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
python manage.py seed_demo_data      # 13 books, 4 bundles, FAQs, legal pages, testimonials...
python manage.py setup_roles         # creates the "Shop Manager" / "Editor" admin groups
python manage.py createsuperuser

python manage.py runserver
```

Visit `http://127.0.0.1:8000/` for the storefront and `http://127.0.0.1:8000/admin/` for the admin panel.

### Running tests

```bash
python -m pytest            # 76 tests, ~7s, uses an in-memory SQLite database
ruff check .                 # lint
```

### Payments (Razorpay)

If `RAZORPAY_KEY_ID` / `RAZORPAY_KEY_SECRET` are **not** set, prepaid checkout runs in
**demo mode**: submitting the checkout form with "Prepaid" immediately marks the order as paid
(clearly flagged to the user), so the full flow is testable without any credentials. **Cash on
Delivery always works** regardless of these keys, since it doesn't touch a payment gateway.

To enable real Razorpay Checkout (test mode):

1. Create a free account at https://dashboard.razorpay.com and grab your **test** keys from
   https://dashboard.razorpay.com/app/keys.
2. Set `RAZORPAY_KEY_ID` and `RAZORPAY_KEY_SECRET` in `.env`.
3. Test card/UPI details are in Razorpay's test-mode docs — any test card with a future expiry
   works in test mode.

### Business settings (prepaid discount, COD fee, GSTIN, etc.)

These are **not** environment variables — they're edited by an Administrator in Django admin
under **Site settings** (singleton), matching the spec's "every business rule is a plugin
setting" principle. Also editable there: **Announcement messages** (the rotating top bar),
**Testimonials**, **FAQs** and **Legal pages**.

## How "Smart Bundles" work

A bundle is a normal `Product` row with `is_bundle=True`, linked to its component books through
`BundleItem` (book + quantity). Its `available_stock` is always computed live as
`min(book.available_stock // item.quantity for item in bundle_items)` — there is no separate
stock number to keep in sync. Buying a bundle deducts stock from each component book (not the
bundle itself); cancelling an order restocks them. This was verified against all the "stock
tests before launch" scenarios from the functionality spec (bundle purchase, buying a book alone,
selling the last copy, cancellation, demo-mode "payment" completion).

## API

Base path: `/api/v1/`

| Endpoint                     | Method    | Auth        | Notes                                |
|-------------------------------|-----------|-------------|----------------------------------------|
| `/categories/`                | GET       | Public      | List active categories                |
| `/products/`                  | GET       | Public      | List/search/filter (`is_bundle`, `category__slug`) |
| `/products/{slug}/`           | GET       | Public      | Product detail (HSN code, stock, images, reviews) |
| `/auth/register/`             | POST      | Public      | Create account                        |
| `/auth/token/`                | POST      | Public      | Obtain JWT access/refresh token pair  |
| `/auth/token/refresh/`        | POST      | Public      | Refresh an access token               |
| `/me/`                        | GET/PATCH | JWT/session | Current user profile                  |
| `/cart/`                      | GET/POST/DELETE | Public (session) | View/add/remove cart items     |
| `/orders/`                    | GET       | JWT/session | Authenticated user's own orders       |

## Deployment

### Option A — Docker (recommended, works anywhere)

```bash
cp .env.example .env   # fill in SECRET_KEY, ALLOWED_HOSTS, Razorpay keys, etc.
docker compose up --build -d
docker compose exec web python manage.py seed_demo_data
docker compose exec web python manage.py setup_roles
docker compose exec web python manage.py createsuperuser
```

Postgres + the Django app (Gunicorn) run as the `web`/`db` services, migrations apply
automatically on startup. Put a reverse proxy (nginx, Caddy, or your platform's built-in one) in
front of port 8000 for TLS termination in production.

### Option B — Render / Railway / Fly.io / Heroku-style platforms

1. Push this repo to GitHub and connect the repository to the platform.
2. Provision a managed PostgreSQL add-on and copy its connection string into `DATABASE_URL`.
3. Set environment variables from `.env.example` — at minimum `SECRET_KEY`, `DEBUG=False`,
   `ALLOWED_HOSTS`, `CSRF_TRUSTED_ORIGINS`, `DATABASE_URL`.
4. Build command: `pip install -r requirements.txt && python manage.py collectstatic --noinput`
5. Release/migrate command: `python manage.py migrate`
6. Start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
7. The `wsgi.py`/`asgi.py` entrypoints already default to `config.settings.prod`.

## CI

`.github/workflows/ci.yml` runs on every push/PR to `main`: installs dependencies, lints with
ruff, runs `manage.py check`, and runs the full pytest suite.

## Known limitations / next steps (also called out in the spec as plugin-level concerns)

- **Shiprocket integration is a data model, not a live API call** — `Order.courier_name`,
  `awb_number` and `tracking_url` are set manually (or by whatever process you wire up) rather
  than through Shiprocket's API, since no Shiprocket account/credentials were supplied. Wiring a
  real Shiprocket webhook to call `apps.orders.services.mark_shipped()` is a small, isolated change.
  Admin's "Mark as delivered" action + the `Order.status` field cover the rest of the fulfilment flow.
- **Tax** is a flat `tax_total` field (default 0) shown as CGST/SGST on the invoice when set —
  wire up real GST-rate logic if/when the business becomes GST-registered.
- **Pincode-level COD/delivery availability checks** (listed as optional in the spec) aren't
  implemented — every PIN code is currently treated as serviceable.
- No Celery/async task queue — Razorpay signature verification and emails run synchronously,
  fine at the spec's stated 4–5 orders/day volume.
