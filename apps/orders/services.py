from decimal import Decimal

import razorpay
from django.conf import settings
from django.db import transaction

from apps.core.models import SiteSettings

from .models import Order, OrderItem


def razorpay_is_configured():
    return bool(settings.RAZORPAY_KEY_ID and settings.RAZORPAY_KEY_SECRET)


def _razorpay_client():
    return razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


@transaction.atomic
def create_order_from_cart(cart, email, shipping_data, payment_method, user=None):
    site_settings = SiteSettings.load()

    order = Order.objects.create(
        user=user,
        email=email,
        payment_method=payment_method,
        shipping_full_name=shipping_data["full_name"],
        shipping_line1=shipping_data["line1"],
        shipping_line2=shipping_data.get("line2", ""),
        shipping_city=shipping_data["city"],
        shipping_state=shipping_data["state"],
        shipping_postal_code=shipping_data["postal_code"],
        shipping_country=shipping_data.get("country", "India"),
        shipping_phone_number=shipping_data.get("phone_number", ""),
        coupon=cart.coupon,
        gstin_snapshot=site_settings.gstin,
        legal_business_name_snapshot=site_settings.legal_business_name,
    )
    for item in cart.items.select_related("product"):
        OrderItem.objects.create(
            order=order,
            product=item.product,
            product_name=item.product.name,
            hsn_code=item.product.hsn_code,
            unit_price=item.product.price,
            quantity=item.quantity,
        )

    order.shipping_cost = Decimal("0.00")  # free shipping on every order, per store policy
    if payment_method == Order.PaymentMethod.COD:
        order.cod_fee = site_settings.cod_fee
    order.recalculate_totals()

    if payment_method == Order.PaymentMethod.PREPAID:
        order.prepaid_discount_total = (order.subtotal * site_settings.prepaid_discount_percent / 100).quantize(
            Decimal("0.01")
        )
        order.recalculate_totals()

    order.status_history.create(status=Order.Status.PENDING_PAYMENT, note="Order created, awaiting confirmation")
    return order


def create_razorpay_order(order):
    client = _razorpay_client()
    rp_order = client.order.create(
        {
            "amount": int(order.total * 100),
            "currency": "INR",
            "receipt": str(order.order_number),
            "notes": {"order_number": str(order.order_number)},
        }
    )
    order.razorpay_order_id = rp_order["id"]
    order.save(update_fields=["razorpay_order_id"])
    return rp_order


def verify_razorpay_payment(order, razorpay_payment_id, razorpay_order_id, razorpay_signature):
    client = _razorpay_client()
    client.utility.verify_payment_signature(
        {
            "razorpay_order_id": razorpay_order_id,
            "razorpay_payment_id": razorpay_payment_id,
            "razorpay_signature": razorpay_signature,
        }
    )
    order.razorpay_payment_id = razorpay_payment_id
    order.razorpay_signature = razorpay_signature
    order.save(update_fields=["razorpay_payment_id", "razorpay_signature"])


@transaction.atomic
def mark_order_processing(order, note="Payment confirmed"):
    """Move an order to Processing and deduct stock — the single "order confirmed" step
    for both a paid prepaid order and a placed COD order."""
    from django.utils import timezone

    if order.status == Order.Status.PROCESSING:
        return
    order.status = Order.Status.PROCESSING
    order.paid_at = timezone.now()
    order.save(update_fields=["status", "paid_at"])
    order.status_history.create(status=Order.Status.PROCESSING, note=note)

    if order.coupon:
        order.coupon.times_used = order.coupon.times_used + 1
        order.coupon.save(update_fields=["times_used"])

    for item in order.items.select_related("product"):
        item.product.deduct_stock(item.quantity)


@transaction.atomic
def cancel_order(order, note="Cancelled"):
    restock = order.status == Order.Status.PROCESSING
    order.status = Order.Status.CANCELLED
    order.save(update_fields=["status"])
    order.status_history.create(status=Order.Status.CANCELLED, note=note)
    if restock:
        for item in order.items.select_related("product"):
            item.product.restock(item.quantity)


@transaction.atomic
def mark_shipped(order, courier_name, awb_number, tracking_url=""):
    from django.utils import timezone

    order.status = Order.Status.SHIPPED
    order.courier_name = courier_name
    order.awb_number = awb_number
    order.tracking_url = tracking_url
    order.shipped_at = timezone.now()
    order.save(update_fields=["status", "courier_name", "awb_number", "tracking_url", "shipped_at"])
    order.status_history.create(status=Order.Status.SHIPPED, note=f"Shipped via {courier_name}, AWB {awb_number}")


@transaction.atomic
def mark_delivered(order):
    from django.utils import timezone

    order.status = Order.Status.DELIVERED
    order.delivered_at = timezone.now()
    order.save(update_fields=["status", "delivered_at"])
    order.status_history.create(status=Order.Status.DELIVERED, note="Delivered")
