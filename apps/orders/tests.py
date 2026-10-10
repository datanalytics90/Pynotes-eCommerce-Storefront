from decimal import Decimal

import pytest
from django.urls import reverse

from apps.cart import services as cart_services
from apps.cart.models import Cart
from apps.core.models import SiteSettings
from apps.orders import services as order_services
from apps.orders.invoice import build_invoice_pdf
from apps.orders.models import Order
from factories import ProductFactory, UserFactory

SHIPPING_DATA = {
    "full_name": "Jane Doe",
    "line1": "123 MG Road",
    "line2": "",
    "city": "Bengaluru",
    "state": "Karnataka",
    "postal_code": "560001",
    "country": "India",
    "phone_number": "9876543210",
}

CHECKOUT_POST_DATA = {
    "first_name": "Jane",
    "last_name": "Doe",
    "phone_number": "9876543210",
    "line1": "123 MG Road",
    "line2": "",
    "city": "Bengaluru",
    "state": "Karnataka",
    "postal_code": "560001",
    "country": "India",
}


@pytest.mark.django_db
class TestOrderServices:
    def test_create_order_from_cart_snapshots_items(self):
        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("499.00"))
        cart_services.add_item(cart, product, 2)

        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.PREPAID
        )

        assert order.items.count() == 1
        assert order.subtotal == Decimal("998.00")
        assert order.status == Order.Status.PENDING_PAYMENT
        assert order.items.first().hsn_code == "4901"

    def test_cod_order_gets_cod_fee(self):
        settings_obj = SiteSettings.load()
        settings_obj.cod_fee = Decimal("49.00")
        settings_obj.save()

        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("499.00"))
        cart_services.add_item(cart, product, 1)
        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.COD
        )
        assert order.cod_fee == Decimal("49.00")
        assert order.total == Decimal("548.00")

    def test_prepaid_order_gets_discount(self):
        settings_obj = SiteSettings.load()
        settings_obj.prepaid_discount_percent = 10
        settings_obj.save()

        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("500.00"))
        cart_services.add_item(cart, product, 1)
        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.PREPAID
        )
        assert order.prepaid_discount_total == Decimal("50.00")
        assert order.total == Decimal("450.00")

    def test_mark_order_processing_deducts_stock(self):
        cart = Cart.objects.create()
        product = ProductFactory(stock=10)
        cart_services.add_item(cart, product, 3)
        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.COD
        )

        order_services.mark_order_processing(order)

        product.refresh_from_db()
        order.refresh_from_db()
        assert product.stock == 7
        assert order.status == Order.Status.PROCESSING
        assert order.paid_at is not None

    def test_mark_order_processing_is_idempotent(self):
        cart = Cart.objects.create()
        product = ProductFactory(stock=10)
        cart_services.add_item(cart, product, 1)
        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.COD
        )

        order_services.mark_order_processing(order)
        order_services.mark_order_processing(order)  # second call should be a no-op

        product.refresh_from_db()
        assert product.stock == 9

    def test_mark_order_processing_deducts_bundle_component_stock(self):
        from apps.catalog.models import BundleItem

        book_a = ProductFactory(stock=10)
        book_b = ProductFactory(stock=10)
        bundle = ProductFactory(is_bundle=True, price=Decimal("899.00"))
        BundleItem.objects.create(bundle=bundle, book=book_a, quantity=1)
        BundleItem.objects.create(bundle=bundle, book=book_b, quantity=1)

        cart = Cart.objects.create()
        cart_services.add_item(cart, bundle, 2)
        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.COD
        )
        order_services.mark_order_processing(order)

        book_a.refresh_from_db()
        book_b.refresh_from_db()
        assert book_a.stock == 8
        assert book_b.stock == 8

    def test_cancel_order_restocks(self):
        cart = Cart.objects.create()
        product = ProductFactory(stock=10)
        cart_services.add_item(cart, product, 3)
        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.COD
        )
        order_services.mark_order_processing(order)
        order_services.cancel_order(order)

        product.refresh_from_db()
        assert product.stock == 10
        assert order.status == Order.Status.CANCELLED

    def test_invoice_pdf_generates(self):
        cart = Cart.objects.create()
        product = ProductFactory(stock=10)
        cart_services.add_item(cart, product, 1)
        order = order_services.create_order_from_cart(
            cart, "buyer@example.com", SHIPPING_DATA, Order.PaymentMethod.COD
        )
        buffer = build_invoice_pdf(order)
        assert buffer.getvalue().startswith(b"%PDF")


@pytest.mark.django_db
class TestCheckoutView:
    def test_checkout_redirects_when_cart_empty(self, client):
        response = client.get(reverse("orders:checkout"))
        assert response.status_code == 302
        assert response.url == reverse("catalog:product_list")

    def test_cod_checkout_creates_processing_order(self, client):
        product = ProductFactory(price=Decimal("499.00"), stock=10)
        client.post(reverse("cart:add_to_cart", kwargs={"slug": product.slug}), {"quantity": 1})

        response = client.post(
            reverse("orders:checkout"),
            {"email": "buyer@example.com", "payment_method": "cod", **CHECKOUT_POST_DATA},
        )

        assert response.status_code == 302
        order = Order.objects.get(email="buyer@example.com")
        assert order.status == Order.Status.PROCESSING
        assert order.payment_method == Order.PaymentMethod.COD
        assert response.url == reverse("orders:success", kwargs={"order_number": order.order_number})

    def test_prepaid_checkout_demo_mode_without_razorpay_keys(self, client, settings):
        settings.RAZORPAY_KEY_ID = ""
        settings.RAZORPAY_KEY_SECRET = ""
        product = ProductFactory(price=Decimal("499.00"), stock=10)
        client.post(reverse("cart:add_to_cart", kwargs={"slug": product.slug}), {"quantity": 1})

        response = client.post(
            reverse("orders:checkout"),
            {"email": "buyer@example.com", "payment_method": "prepaid", **CHECKOUT_POST_DATA},
        )

        assert response.status_code == 302
        order = Order.objects.get(email="buyer@example.com")
        assert order.status == Order.Status.PROCESSING
        assert response.url == reverse("orders:success", kwargs={"order_number": order.order_number})

    def test_order_history_requires_login(self, client):
        response = client.get(reverse("orders:order_history"))
        assert response.status_code == 302

    def test_order_history_lists_own_orders_only(self, client):
        user = UserFactory()
        other_user = UserFactory()
        Order.objects.create(user=user, email=user.email, **_order_shipping_kwargs())
        Order.objects.create(user=other_user, email=other_user.email, **_order_shipping_kwargs())

        client.force_login(user)
        response = client.get(reverse("orders:order_history"))
        assert len(response.context["orders"]) == 1

    def test_download_invoice_requires_ownership(self, client):
        owner = UserFactory()
        other = UserFactory()
        order = Order.objects.create(user=owner, email=owner.email, **_order_shipping_kwargs())
        client.force_login(other)
        response = client.get(reverse("orders:download_invoice", kwargs={"order_number": order.order_number}))
        assert response.status_code == 404


@pytest.mark.django_db
class TestOrderTracking:
    def test_guest_can_track_order_by_number_and_email(self, client):
        order = Order.objects.create(email="guest@example.com", **_order_shipping_kwargs())
        response = client.post(
            reverse("orders:order_tracking"),
            {"order_number": str(order.order_number), "email": "guest@example.com"},
        )
        assert response.status_code == 200
        assert response.context["order"] == order

    def test_tracking_fails_with_wrong_email(self, client):
        order = Order.objects.create(email="guest@example.com", **_order_shipping_kwargs())
        response = client.post(
            reverse("orders:order_tracking"),
            {"order_number": str(order.order_number), "email": "wrong@example.com"},
        )
        assert response.context["order"] is None


def _order_shipping_kwargs():
    return {
        "shipping_full_name": "Jane Doe",
        "shipping_line1": "123 MG Road",
        "shipping_city": "Bengaluru",
        "shipping_state": "Karnataka",
        "shipping_postal_code": "560001",
        "shipping_country": "India",
    }
