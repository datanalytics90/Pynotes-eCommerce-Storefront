from decimal import Decimal

import factory
from django.utils import timezone

from apps.accounts.models import Address, User
from apps.catalog.models import BundleItem, Category, Coupon, Product


class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User
        skip_postgeneration_save = True

    email = factory.Sequence(lambda n: f"user{n}@example.com")
    first_name = "Test"
    last_name = "User"

    @factory.post_generation
    def password(self, create, extracted, **kwargs):
        self.set_password(extracted or "testpass123")
        if create:
            self.save()


class AddressFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Address

    user = factory.SubFactory(UserFactory)
    full_name = "Jane Doe"
    line1 = "123 Main St"
    city = "Bengaluru"
    state = "Karnataka"
    postal_code = "560001"
    country = "India"
    is_default = True


class CategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Category

    name = factory.Sequence(lambda n: f"Category {n}")


class ProductFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Product

    category = factory.SubFactory(CategoryFactory)
    name = factory.Sequence(lambda n: f"Product {n}")
    description = "A great printed coding-notes book for testing."
    short_description = "Great book."
    price = Decimal("499.00")
    sku = factory.Sequence(lambda n: f"PYN-{n}")
    stock = 10
    hsn_code = "4901"
    is_active = True
    is_bundle = False


class BundleItemFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BundleItem

    bundle = factory.SubFactory(ProductFactory, is_bundle=True)
    book = factory.SubFactory(ProductFactory)
    quantity = 1


class CouponFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Coupon

    code = factory.Sequence(lambda n: f"CODE{n}")
    discount_percent = 10
    active = True
    valid_from = factory.LazyFunction(lambda: timezone.now() - timezone.timedelta(days=1))
    valid_to = factory.LazyFunction(lambda: timezone.now() + timezone.timedelta(days=30))
