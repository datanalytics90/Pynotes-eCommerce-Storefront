from apps.catalog.models import Category

from .models import AnnouncementMessage, SiteSettings


def site_settings(request):
    settings_obj = SiteSettings.load()
    return {
        "SITE_NAME": settings_obj.site_name,
        "site_settings": settings_obj,
        "nav_categories": Category.objects.filter(is_active=True, parent__isnull=True)
        .prefetch_related("children")
        .order_by("order", "name")[:8],
        "announcement_messages": AnnouncementMessage.objects.filter(is_active=True).order_by("order"),
    }
