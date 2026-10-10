from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.core.management.base import BaseCommand

SHOP_MANAGER_MODELS = [
    ("catalog", "product"),
    ("catalog", "category"),
    ("catalog", "bundleitem"),
    ("catalog", "productimage"),
    ("catalog", "review"),
    ("catalog", "coupon"),
    ("orders", "order"),
    ("orders", "orderitem"),
    ("orders", "issuereport"),
    ("core", "contactmessage"),
]

EDITOR_MODELS = [
    ("core", "testimonial"),
    ("core", "faq"),
    ("core", "announcementmessage"),
    ("core", "legalpage"),
    ("catalog", "category"),
    ("catalog", "product"),
]


def _permissions_for(models, actions=("add", "change", "view", "delete")):
    perms = []
    for app_label, model in models:
        try:
            ct = ContentType.objects.get(app_label=app_label, model=model)
        except ContentType.DoesNotExist:
            continue
        for action in actions:
            try:
                perms.append(Permission.objects.get(content_type=ct, codename=f"{action}_{model}"))
            except Permission.DoesNotExist:
                continue
    return perms


class Command(BaseCommand):
    help = "Creates the 'Shop Manager' and 'Editor' admin roles (Django Groups) from the functionality spec."

    def handle(self, *args, **options):
        shop_manager, _ = Group.objects.get_or_create(name="Shop Manager")
        shop_manager.permissions.set(_permissions_for(SHOP_MANAGER_MODELS))

        editor, _ = Group.objects.get_or_create(name="Editor")
        editor.permissions.set(_permissions_for(EDITOR_MODELS, actions=("add", "change", "view")))

        self.stdout.write(self.style.SUCCESS("Shop Manager and Editor groups configured."))
