from django.conf import settings

from apps.catalog.models import Category


def site_settings(request):
    return {
        "SITE_NAME": settings.SITE_NAME,
        "nav_categories": Category.objects.filter(is_active=True).order_by("order", "name")[:8],
    }
