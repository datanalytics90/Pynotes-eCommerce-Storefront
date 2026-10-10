from decimal import Decimal

import pytest
from django.urls import reverse

from apps.cart import services as cart_services
from apps.cart.models import Cart
from apps.orders import services as order_services
from apps.orders.models import Order
from factories import ProductFactory, UserFactory

SHIPPING_DATA = {
    "full_name": "Jane Doe",
    "line1": "123 Main St",
    "line2": "",
    "city": "Springfield",
    "state": "IL",
    "postal_code": "62704",
    "country": "United States",
    "phone_number": "",
}


@pytest.mark.django_db
class TestOrderServices:
    def test_create_order_from_cart_snapshots_items(self):
        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("25.00"), is_digital=True)
        cart_services.add_item(cart, product, 2)

        order = order_services.create_order_from_cart(cart, "buyer@example.com", SHIPPING_DATA)

        assert order.items.count() == 1
        assert order.subtotal == Decimal("50.00")
        assert order.status == Order.Status.PENDING
        assert order.shipping_cost == Decimal("0.00")  # digital-only order

    def test_physical_order_gets_shipping_cost(self):
        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("25.00"), is_digital=False, stock=10)
        cart_services.add_item(cart, product, 1)

        order = order_services.create_order_from_cart(cart, "buyer@example.com", SHIPPING_DATA)
        assert order.shipping_cost == Decimal("5.00")

    def test_mark_order_paid_decrements_stock_for_physical_products(self):
        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("10.00"), is_digital=False, stock=10)
        cart_services.add_item(cart, product, 3)
        order = order_services.create_order_from_cart(cart, "buyer@example.com", SHIPPING_DATA)

        order_services.mark_order_paid(order)

        product.refresh_from_db()
        order.refresh_from_db()
        assert product.stock == 7
        assert order.status == Order.Status.PAID
        assert order.paid_at is not None

    def test_mark_order_paid_is_idempotent(self):
        cart = Cart.objects.create()
        product = ProductFactory(is_digital=False, stock=10)
        cart_services.add_item(cart, product, 1)
        order = order_services.create_order_from_cart(cart, "buyer@example.com", SHIPPING_DATA)

        order_services.mark_order_paid(order)
        order_services.mark_order_paid(order)  # second call should be a no-op

        product.refresh_from_db()
        assert product.stock == 9


@pytest.mark.django_db
class TestCheckoutView:
    def test_checkout_redirects_when_cart_empty(self, client):
        response = client.get(reverse("orders:checkout"))
        assert response.status_code == 302
        assert response.url == reverse("catalog:product_list")

    def test_checkout_demo_mode_creates_paid_order(self, client, settings):
        settings.STRIPE_SECRET_KEY = ""
        product = ProductFactory(price=Decimal("15.00"), is_digital=True)
        client.post(reverse("cart:add_to_cart", kwargs={"slug": product.slug}), {"quantity": 1})

        response = client.post(
            reverse("orders:checkout"),
            {"email": "buyer@example.com", **SHIPPING_DATA},
        )

        assert response.status_code == 302
        order = Order.objects.get(email="buyer@example.com")
        assert order.status == Order.Status.PAID
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


def _order_shipping_kwargs():
    return {
        "shipping_full_name": "Jane Doe",
        "shipping_line1": "123 Main St",
        "shipping_city": "Springfield",
        "shipping_state": "IL",
        "shipping_postal_code": "62704",
        "shipping_country": "United States",
    }
