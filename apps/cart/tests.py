from decimal import Decimal

import pytest
from django.urls import reverse

from apps.cart import services
from apps.cart.models import Cart
from factories import CouponFactory, ProductFactory, UserFactory


@pytest.mark.django_db
class TestCartServices:
    def test_add_item_creates_and_increments(self):
        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("10.00"), stock=5)
        services.add_item(cart, product, 2)
        services.add_item(cart, product, 3)
        item = cart.items.get(product=product)
        assert item.quantity == 5
        assert cart.subtotal == Decimal("50.00")

    def test_set_item_quantity_zero_removes_item(self):
        cart = Cart.objects.create()
        product = ProductFactory()
        services.add_item(cart, product, 1)
        services.set_item_quantity(cart, product, 0)
        assert cart.items.count() == 0

    def test_merge_carts_combines_quantities(self):
        user = UserFactory()
        guest_cart = Cart.objects.create(session_key="guest-session")
        user_cart = Cart.objects.create(user=user)
        product = ProductFactory()
        services.add_item(guest_cart, product, 2)
        services.add_item(user_cart, product, 1)
        services.merge_carts(source=guest_cart, destination=user_cart)
        assert user_cart.items.get(product=product).quantity == 3
        assert not Cart.objects.filter(pk=guest_cart.pk).exists()

    def test_coupon_discount_applied(self):
        cart = Cart.objects.create()
        product = ProductFactory(price=Decimal("100.00"))
        services.add_item(cart, product, 1)
        cart.coupon = CouponFactory(discount_percent=20)
        cart.save()
        assert cart.discount_total == Decimal("20.00")
        assert cart.total == Decimal("80.00")


@pytest.mark.django_db
class TestCartViews:
    def test_add_to_cart_redirects_and_increments_badge(self, client):
        product = ProductFactory(stock=5)
        response = client.post(reverse("cart:add_to_cart", kwargs={"slug": product.slug}), {"quantity": 2})
        assert response.status_code == 302
        cart_response = client.get(reverse("cart:cart_detail"))
        assert b"2" in cart_response.content

    def test_add_out_of_stock_product_shows_error(self, client):
        product = ProductFactory(stock=0)
        response = client.post(
            reverse("cart:add_to_cart", kwargs={"slug": product.slug}), {"quantity": 1}, follow=True
        )
        messages = list(response.context["messages"])
        assert any("out of stock" in str(m) for m in messages)

    def test_remove_from_cart(self, client):
        product = ProductFactory()
        client.post(reverse("cart:add_to_cart", kwargs={"slug": product.slug}), {"quantity": 1})
        client.post(reverse("cart:remove_from_cart", kwargs={"product_id": product.id}))
        response = client.get(reverse("cart:cart_detail"))
        assert b"Your cart is empty" in response.content

    def test_apply_invalid_coupon_shows_error(self, client):
        response = client.post(reverse("cart:apply_coupon"), {"code": "NOPE"}, follow=True)
        messages = list(response.context["messages"])
        assert any("not valid" in str(m) for m in messages)

    def test_apply_valid_coupon(self, client):
        CouponFactory(code="SAVE20", discount_percent=20)
        response = client.post(reverse("cart:apply_coupon"), {"code": "SAVE20"}, follow=True)
        messages = list(response.context["messages"])
        assert any("applied" in str(m) for m in messages)

    def test_buy_now_adds_item_and_redirects_to_checkout(self, client):
        product = ProductFactory(stock=5)
        response = client.post(reverse("cart:buy_now", kwargs={"slug": product.slug}), {"quantity": 1})
        assert response.status_code == 302
        assert response.url == reverse("orders:checkout")
        cart_response = client.get(reverse("cart:cart_detail"))
        assert product.name.encode() in cart_response.content
