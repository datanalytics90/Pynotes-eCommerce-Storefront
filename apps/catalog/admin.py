from django.contrib import admin

from .models import BundleItem, Category, Coupon, Product, ProductImage, Review


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1


class BundleItemInline(admin.TabularInline):
    model = BundleItem
    fk_name = "bundle"
    extra = 1
    autocomplete_fields = ["book"]
    verbose_name = "Book in this bundle"
    verbose_name_plural = "Books in this bundle (only used when 'Is bundle' is checked)"


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "parent", "slug", "is_active", "order"]
    list_filter = ["parent"]
    list_editable = ["order", "is_active"]
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name"]
    autocomplete_fields = ["parent"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        "name", "category", "price", "is_bundle", "stock_display", "is_active", "is_featured", "created_at",
    ]
    list_filter = ["category", "is_active", "is_featured", "is_bundle"]
    list_editable = ["price", "is_active", "is_featured"]
    search_fields = ["name", "sku", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, BundleItemInline]
    autocomplete_fields = ["category"]
    fieldsets = (
        (None, {"fields": ("category", "name", "slug", "sku", "is_active", "is_featured")}),
        ("Description", {"fields": ("short_description", "description")}),
        ("Pricing", {"fields": ("price", "compare_at_price")}),
        (
            "Stock & bundling",
            {
                "fields": ("is_bundle", "stock", "weight_kg", "hsn_code"),
                "description": "For a bundle, tick 'Is bundle' and add its books below — the Stock field "
                "above is then ignored and availability is computed from the component books.",
            },
        ),
    )

    @admin.display(description="Stock")
    def stock_display(self, obj):
        if obj.is_bundle:
            return f"{obj.available_stock} (from books)"
        return obj.stock


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["product", "user", "rating", "is_approved", "created_at"]
    list_filter = ["rating", "is_approved"]
    search_fields = ["product__name", "user__email", "title"]
    actions = ["approve_reviews"]

    @admin.action(description="Approve selected reviews")
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ["code", "discount_percent", "active", "valid_from", "valid_to", "times_used", "usage_limit"]
    list_filter = ["active"]
    search_fields = ["code"]
