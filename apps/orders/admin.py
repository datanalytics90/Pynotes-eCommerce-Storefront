from django.contrib import admin
from django.utils import timezone

from . import services
from .models import IssueReport, Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "hsn_code", "unit_price", "quantity"]
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["status", "note", "created_at"]
    can_delete = False


class IssueReportInline(admin.TabularInline):
    model = IssueReport
    extra = 0
    readonly_fields = ["description", "photo", "was_within_window", "created_at"]
    fields = ["description", "photo", "was_within_window", "is_resolved", "resolution_note", "created_at"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        "order_number", "email", "payment_method", "status", "cod_confirmed", "total", "created_at",
    ]
    list_filter = ["status", "payment_method", "cod_confirmed", "created_at"]
    search_fields = ["order_number", "email", "user__email", "awb_number"]
    readonly_fields = [
        "order_number",
        "subtotal",
        "discount_total",
        "prepaid_discount_total",
        "cod_fee",
        "total",
        "razorpay_order_id",
        "razorpay_payment_id",
        "razorpay_signature",
        "created_at",
        "updated_at",
        "paid_at",
        "shipped_at",
        "delivered_at",
    ]
    fieldsets = (
        (None, {"fields": ("order_number", "user", "email", "status", "payment_method")}),
        (
            "Shipping address",
            {
                "fields": (
                    "shipping_full_name", "shipping_line1", "shipping_line2", "shipping_city",
                    "shipping_state", "shipping_postal_code", "shipping_country", "shipping_phone_number",
                )
            },
        ),
        (
            "Totals",
            {
                "fields": (
                    "subtotal", "discount_total", "prepaid_discount_total", "cod_fee",
                    "shipping_cost", "tax_total", "total",
                )
            },
        ),
        ("COD confirmation", {"fields": ("cod_confirmed", "cod_confirmed_at")}),
        ("Fulfilment / tracking", {"fields": ("courier_name", "awb_number", "tracking_url")}),
        ("Payment reference", {"fields": ("razorpay_order_id", "razorpay_payment_id", "razorpay_signature")}),
        ("GST snapshot", {"fields": ("gstin_snapshot", "legal_business_name_snapshot")}),
        ("Timestamps", {"fields": ("created_at", "updated_at", "paid_at", "shipped_at", "delivered_at")}),
    )
    inlines = [OrderItemInline, IssueReportInline, OrderStatusHistoryInline]
    actions = [
        "confirm_cod",
        "cancel_unconfirmed_cod",
        "mark_as_delivered",
    ]

    @admin.action(description="Confirm COD order (phoned/WhatsApped customer)")
    def confirm_cod(self, request, queryset):
        updated = queryset.filter(payment_method=Order.PaymentMethod.COD).update(
            cod_confirmed=True, cod_confirmed_at=timezone.now()
        )
        self.message_user(request, f"{updated} order(s) marked COD-confirmed.")

    @admin.action(description="Cancel unconfirmed COD order (restocks)")
    def cancel_unconfirmed_cod(self, request, queryset):
        for order in queryset.filter(payment_method=Order.PaymentMethod.COD, cod_confirmed=False):
            services.cancel_order(order, note="Cancelled: COD customer could not be reached")

    @admin.action(description="Mark selected orders as delivered")
    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            services.mark_delivered(order)

    def save_model(self, request, obj, form, change):
        previous_status = None
        if change:
            previous_status = Order.objects.get(pk=obj.pk).status
        super().save_model(request, obj, form, change)
        if previous_status and previous_status != obj.status:
            obj.status_history.create(status=obj.status, note="Status changed via admin")
            if obj.status == Order.Status.SHIPPED and not obj.shipped_at:
                obj.shipped_at = timezone.now()
                obj.save(update_fields=["shipped_at"])
            if obj.status == Order.Status.DELIVERED and not obj.delivered_at:
                obj.delivered_at = timezone.now()
                obj.save(update_fields=["delivered_at"])
            if obj.status == Order.Status.CANCELLED and previous_status == Order.Status.PROCESSING:
                for item in obj.items.select_related("product"):
                    item.product.restock(item.quantity)
