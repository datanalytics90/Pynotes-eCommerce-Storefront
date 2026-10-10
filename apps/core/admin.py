from django.contrib import admin

from .models import FAQ, AnnouncementMessage, ContactMessage, LegalPage, SiteSettings, Testimonial


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ["name", "email", "subject", "is_read", "created_at"]
    list_filter = ["is_read"]
    search_fields = ["name", "email", "subject", "message"]
    readonly_fields = ["name", "email", "subject", "message", "created_at"]


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(AnnouncementMessage)
class AnnouncementMessageAdmin(admin.ModelAdmin):
    list_display = ["text", "is_active", "order"]
    list_editable = ["is_active", "order"]


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ["author_name", "platform", "is_active", "order"]
    list_editable = ["is_active", "order"]
    search_fields = ["author_name", "quote"]
    filter_horizontal = ["products"]


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ["question", "group", "order", "is_active"]
    list_filter = ["group", "is_active"]
    list_editable = ["order", "is_active"]
    search_fields = ["question", "answer"]


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ["title", "slug", "updated_at"]
