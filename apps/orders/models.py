import uuid
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.catalog.models import Coupon, Product


class Order(models.Model):
    class Status(models.TextChoices):
        PENDING_PAYMENT = "pending_payment", "Pending payment"
        PROCESSING = "processing", "Processing"
        ON_HOLD = "on_hold", "On hold"
        SHIPPED = "shipped", "Shipped"
        DELIVERED = "delivered", "Delivered"
        CANCELLED = "cancelled", "Cancelled"
        REFUNDED = "refunded", "Refunded"
        FAILED = "failed", "Failed"

    class PaymentMethod(models.TextChoices):
        PREPAID = "prepaid", "Prepaid (Razorpay)"
        COD = "cod", "Cash on Delivery"

    order_number = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="orders"
    )
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING_PAYMENT)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.PREPAID)

    shipping_full_name = models.CharField(max_length=150)
    shipping_line1 = models.CharField(max_length=255)
    shipping_line2 = models.CharField(max_length=255, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=100)
    shipping_postal_code = models.CharField(max_length=20)
    shipping_country = models.CharField(max_length=100, default="India")
    shipping_phone_number = models.CharField(max_length=20, blank=True)

    coupon = models.ForeignKey(Coupon, on_delete=models.SET_NULL, null=True, blank=True)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    prepaid_discount_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    cod_fee = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    shipping_cost = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    tax_total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    total = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))

    # GST invoice snapshot (so later changes to site settings don't rewrite history)
    gstin_snapshot = models.CharField(max_length=15, blank=True)
    legal_business_name_snapshot = models.CharField(max_length=200, blank=True)

    # Razorpay (prepaid)
    razorpay_order_id = models.CharField(max_length=255, blank=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True)
    razorpay_signature = models.CharField(max_length=255, blank=True)

    # COD confirmation (phone/WhatsApp call before shipping)
    cod_confirmed = models.BooleanField(default=False)
    cod_confirmed_at = models.DateTimeField(null=True, blank=True)

    # Shiprocket-style fulfilment/tracking
    courier_name = models.CharField(max_length=100, blank=True)
    awb_number = models.CharField(max_length=100, blank=True)
    tracking_url = models.URLField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    shipped_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Order {self.order_number} ({self.get_status_display()})"

    def recalculate_totals(self):
        self.subtotal = sum((item.line_total for item in self.items.all()), Decimal("0.00"))
        if self.coupon and self.coupon.is_valid():
            self.discount_total = (self.subtotal * self.coupon.discount_percent / 100).quantize(Decimal("0.01"))
        self.total = (
            self.subtotal
            - self.discount_total
            - self.prepaid_discount_total
            + self.cod_fee
            + self.shipping_cost
            + self.tax_total
        )
        self.save(
            update_fields=[
                "subtotal", "discount_total", "prepaid_discount_total", "cod_fee", "shipping_cost", "total",
            ]
        )

    @property
    def is_paid(self):
        return self.status not in (
            Order.Status.PENDING_PAYMENT,
            Order.Status.CANCELLED,
            Order.Status.FAILED,
        )

    @property
    def issue_window_open(self):
        from django.utils import timezone

        from apps.core.models import SiteSettings

        if not self.delivered_at:
            return False
        hours = SiteSettings.load().issue_window_hours
        return timezone.now() <= self.delivered_at + timezone.timedelta(hours=hours)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="order_items")
    product_name = models.CharField(max_length=200)
    hsn_code = models.CharField(max_length=10, blank=True)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        return f"{self.quantity} x {self.product_name}"

    @property
    def line_total(self):
        return self.unit_price * self.quantity


class OrderStatusHistory(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="status_history")
    status = models.CharField(max_length=20, choices=Order.Status.choices)
    note = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "order status histories"

    def __str__(self):
        return f"{self.order.order_number} -> {self.status}"


class IssueReport(models.Model):
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="issue_reports")
    description = models.TextField()
    photo = models.ImageField(upload_to="issue_reports/", blank=True, null=True)
    was_within_window = models.BooleanField(default=True)
    is_resolved = models.BooleanField(default=False)
    resolution_note = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Issue on {self.order.order_number}"
