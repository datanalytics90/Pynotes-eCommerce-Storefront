from django.contrib import admin

from .models import Order, OrderItem, OrderStatusHistory


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ["product", "product_name", "unit_price", "quantity"]
    can_delete = False


class OrderStatusHistoryInline(admin.TabularInline):
    model = OrderStatusHistory
    extra = 0
    readonly_fields = ["status", "note", "created_at"]
    can_delete = False


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_number", "email", "status", "total", "created_at", "paid_at"]
    list_filter = ["status", "created_at"]
    search_fields = ["order_number", "email", "user__email"]
    readonly_fields = [
        "order_number",
        "subtotal",
        "discount_total",
        "total",
        "stripe_payment_intent_id",
        "stripe_checkout_session_id",
        "created_at",
        "updated_at",
        "paid_at",
    ]
    inlines = [OrderItemInline, OrderStatusHistoryInline]
    actions = ["mark_as_shipped", "mark_as_delivered"]

    @admin.action(description="Mark selected orders as shipped")
    def mark_as_shipped(self, request, queryset):
        for order in queryset:
            order.status = Order.Status.SHIPPED
            order.save(update_fields=["status"])
            order.status_history.create(status=Order.Status.SHIPPED, note="Marked shipped via admin action")

    @admin.action(description="Mark selected orders as delivered")
    def mark_as_delivered(self, request, queryset):
        for order in queryset:
            order.status = Order.Status.DELIVERED
            order.save(update_fields=["status"])
            order.status_history.create(status=Order.Status.DELIVERED, note="Marked delivered via admin action")
