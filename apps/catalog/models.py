from decimal import Decimal

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.urls import reverse
from django.utils.text import slugify


class Category(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to="categories/", blank=True, null=True)
    parent = models.ForeignKey(
        "self", on_delete=models.CASCADE, null=True, blank=True, related_name="children"
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name) or "category"
            slug = base_slug
            counter = 1
            while Category.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:category_detail", kwargs={"slug": self.slug})


class Product(models.Model):
    """A printed subject book, or a Smart Bundle of several books.

    Bundles are themselves Product rows (is_bundle=True) linked to their
    component books through BundleItem. A bundle's own `stock` field is not
    used for availability — its stock is always derived live from the books
    inside it, matching the reference store's "bundle stock follows the
    books" rule.
    """

    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=220, unique=True, blank=True)
    description = models.TextField()
    short_description = models.CharField(max_length=300, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal("0.01"))])
    compare_at_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    stock = models.PositiveIntegerField(
        default=0, help_text="Ignored for bundles — bundle stock is computed from its books."
    )
    hsn_code = models.CharField(
        max_length=10, blank=True, default="4901", help_text="HSN code for the GST invoice (printed books: 4901)."
    )
    is_bundle = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    weight_kg = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["slug"]), models.Index(fields=["is_active", "is_featured"])]

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.slug:
            base_slug = slugify(self.name)
            slug = base_slug
            counter = 1
            while Product.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                slug = f"{base_slug}-{counter}"
                counter += 1
            self.slug = slug
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse("catalog:product_detail", kwargs={"slug": self.slug})

    @property
    def available_stock(self):
        """Live stock: derived from component books for a bundle, else the stored value."""
        if not self.is_bundle:
            return self.stock
        items = list(self.bundle_items.select_related("book"))
        if not items:
            return 0
        return min(item.book.available_stock // item.quantity for item in items)

    @property
    def in_stock(self):
        return self.available_stock > 0

    @property
    def discount_percent(self):
        if self.compare_at_price and self.compare_at_price > self.price:
            return int(round((self.compare_at_price - self.price) / self.compare_at_price * 100))
        return 0

    @property
    def average_rating(self):
        agg = self.reviews.filter(is_approved=True).aggregate(models.Avg("rating"))
        return round(agg["rating__avg"] or 0, 1)

    @property
    def review_count(self):
        return self.reviews.filter(is_approved=True).count()

    def deduct_stock(self, quantity):
        """Deduct stock for an order of `quantity` units of this product."""
        if self.is_bundle:
            for item in self.bundle_items.select_related("book"):
                book = item.book
                book.stock = max(book.stock - item.quantity * quantity, 0)
                book.save(update_fields=["stock"])
        else:
            self.stock = max(self.stock - quantity, 0)
            self.save(update_fields=["stock"])

    def restock(self, quantity):
        """Reverse of deduct_stock, used when an order is cancelled/refunded."""
        if self.is_bundle:
            for item in self.bundle_items.select_related("book"):
                book = item.book
                book.stock = book.stock + item.quantity * quantity
                book.save(update_fields=["stock"])
        else:
            self.stock = self.stock + quantity
            self.save(update_fields=["stock"])


class BundleItem(models.Model):
    bundle = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="bundle_items")
    book = models.ForeignKey(Product, on_delete=models.PROTECT, related_name="in_bundles")
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("bundle", "book")
        ordering = ["id"]

    def __str__(self):
        return f"{self.bundle.name} <- {self.quantity} x {self.book.name}"


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField(upload_to="products/")
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.product.name} image #{self.pk}"

    def save(self, *args, **kwargs):
        if self.is_primary:
            ProductImage.objects.filter(product=self.product).exclude(pk=self.pk).update(is_primary=False)
        super().save(*args, **kwargs)


class Review(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=150, blank=True)
    body = models.TextField(blank=True)
    is_approved = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        unique_together = ("product", "user")

    def __str__(self):
        return f"{self.rating}★ review of {self.product.name} by {self.user.email}"


class Coupon(models.Model):
    code = models.CharField(max_length=40, unique=True)
    discount_percent = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(100)])
    active = models.BooleanField(default=True)
    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()
    usage_limit = models.PositiveIntegerField(default=0, help_text="0 = unlimited")
    times_used = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.code

    def is_valid(self):
        from django.utils import timezone

        now = timezone.now()
        if not self.active or not (self.valid_from <= now <= self.valid_to):
            return False
        if self.usage_limit and self.times_used >= self.usage_limit:
            return False
        return True
