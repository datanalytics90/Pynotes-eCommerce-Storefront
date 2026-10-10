from decimal import Decimal

import stripe
from django.conf import settings
from django.db import transaction
from django.urls import reverse

from .models import Order, OrderItem

stripe.api_key = settings.STRIPE_SECRET_KEY


@transaction.atomic
def create_order_from_cart(cart, email, shipping_data, user=None):
    order = Order.objects.create(
        user=user,
        email=email,
        coupon=cart.coupon,
        shipping_full_name=shipping_data["full_name"],
        shipping_line1=shipping_data["line1"],
        shipping_line2=shipping_data.get("line2", ""),
        shipping_city=shipping_data["city"],
        shipping_state=shipping_data["state"],
        shipping_postal_code=shipping_data["postal_code"],
        shipping_country=shipping_data["country"],
        shipping_phone_number=shipping_data.get("phone_number", ""),
    )
    for item in cart.items.select_related("product"):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            unit_price=item.product.price,
            quantity=item.quantity,
        )
    has_physical_items = any(not item.product.is_digital for item in cart.items.select_related("product"))
    order.shipping_cost = Decimal("5.00") if has_physical_items and cart.subtotal > 0 else Decimal("0.00")
    order.recalculate_totals()
    order.status_history.create(status=Order.Status.PENDING, note="Order created, awaiting payment")
    return order


def stripe_is_configured():
    return bool(settings.STRIPE_SECRET_KEY)


def create_checkout_session(order, request):
    line_items = [
        {
            "price_data": {
                "currency": settings.CURRENCY,
                "product_data": {"name": item.product_name},
                "unit_amount": int(item.unit_price * 100),
            },
            "quantity": item.quantity,
        }
        for item in order.items.all()
    ]
    if order.shipping_cost:
        line_items.append(
            {
                "price_data": {
                    "currency": settings.CURRENCY,
                    "product_data": {"name": "Shipping"},
                    "unit_amount": int(order.shipping_cost * 100),
                },
                "quantity": 1,
            }
        )

    success_url = request.build_absolute_uri(
        reverse("orders:success", kwargs={"order_number": order.order_number})
    ) + "?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = request.build_absolute_uri(reverse("orders:checkout"))

    session = stripe.checkout.Session.create(
        mode="payment",
        payment_method_types=["card"],
        line_items=line_items,
        customer_email=order.email,
        success_url=success_url,
        cancel_url=cancel_url,
        metadata={"order_number": str(order.order_number)},
    )
    order.stripe_checkout_session_id = session.id
    order.save(update_fields=["stripe_checkout_session_id"])
    return session


def mark_order_paid(order, payment_intent_id=""):
    from django.utils import timezone

    if order.status == Order.Status.PAID:
        return
    order.status = Order.Status.PAID
    order.paid_at = timezone.now()
    if payment_intent_id:
        order.stripe_payment_intent_id = payment_intent_id
    order.save(update_fields=["status", "paid_at", "stripe_payment_intent_id"])
    order.status_history.create(status=Order.Status.PAID, note="Payment confirmed")

    if order.coupon:
        order.coupon.times_used = order.coupon.times_used + 1
        order.coupon.save(update_fields=["times_used"])

    for item in order.items.select_related("product"):
        product = item.product
        if not product.is_digital:
            product.stock = max(product.stock - item.quantity, 0)
            product.save(update_fields=["stock"])
