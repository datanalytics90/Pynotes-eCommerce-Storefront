from decimal import Decimal

from django.db import models


class ContactMessage(models.Model):
    name = models.CharField(max_length=150)
    email = models.EmailField()
    subject = models.CharField(max_length=200)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.subject} from {self.email}"


class SiteSettings(models.Model):
    """Singleton: the admin-editable "Site Settings" options page from the spec.

    Business rules (prepaid discount %, COD fee, GST details) live here so
    they are plugin-style settings, not hard-coded values.
    """

    site_name = models.CharField(max_length=100, default="PyNotes")
    tagline = models.CharField(max_length=200, default="Learn. Write. Grow.")
    support_email = models.EmailField(default="support@pynotes.store")
    whatsapp_number = models.CharField(max_length=20, blank=True)

    legal_business_name = models.CharField(max_length=200, blank=True, default="PyNotes")
    gstin = models.CharField(max_length=15, blank=True, help_text="Leave blank if not GST-registered yet.")

    prepaid_discount_percent = models.PositiveSmallIntegerField(
        default=10, help_text="Extra % off applied automatically for prepaid (Razorpay) checkout."
    )
    cod_fee = models.DecimalField(
        max_digits=8, decimal_places=2, default=Decimal("49.00"), help_text="Flat fee added to Cash on Delivery orders."
    )
    free_shipping_note = models.CharField(max_length=200, default="Free shipping on every order.")
    processing_note = models.CharField(max_length=200, default="Processed in 1 to 2 business days.")
    delivery_note = models.CharField(max_length=200, default="Delivered in 3 to 7 business days.")
    issue_window_hours = models.PositiveIntegerField(
        default=48, help_text="Hours after delivery a damaged/wrong-item report is considered on time."
    )

    class Meta:
        verbose_name = "Site settings"
        verbose_name_plural = "Site settings"

    def __str__(self):
        return "Site settings"

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        pass

    @classmethod
    def load(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class AnnouncementMessage(models.Model):
    text = models.CharField(max_length=200)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.text


class Testimonial(models.Model):
    author_name = models.CharField(max_length=150)
    avatar = models.ImageField(upload_to="testimonials/", blank=True, null=True)
    quote = models.TextField()
    platform = models.CharField(max_length=50, blank=True, help_text="e.g. Google, Instagram, Email")
    products = models.ManyToManyField("catalog.Product", blank=True, related_name="testimonials")
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "-created_at"]

    def __str__(self):
        return f"{self.author_name} — {self.quote[:40]}"


class FAQ(models.Model):
    class Group(models.TextChoices):
        GENERAL = "general", "General"
        ORDERING = "ordering", "Ordering"
        SHIPPING = "shipping", "Shipping"
        PAYMENTS = "payments", "Payments"
        RETURNS = "returns", "Returns"

    question = models.CharField(max_length=255)
    answer = models.TextField()
    group = models.CharField(max_length=20, choices=Group.choices, default=Group.GENERAL)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["group", "order", "id"]
        verbose_name = "FAQ"
        verbose_name_plural = "FAQs"

    def __str__(self):
        return self.question


class LegalPage(models.Model):
    class Slug(models.TextChoices):
        PRIVACY = "privacy", "Privacy Policy"
        TERMS = "terms", "Terms & Conditions"
        SHIPPING = "shipping", "Shipping Policy"
        REFUND = "refund", "Refund & Cancellation Policy"

    slug = models.CharField(max_length=20, choices=Slug.choices, unique=True)
    title = models.CharField(max_length=200)
    body = models.TextField(help_text="Plain text/paragraphs; line breaks are preserved on the page.")
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        from django.urls import reverse

        return reverse("core:legal_page", kwargs={"slug": self.slug})
