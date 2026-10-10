from decimal import Decimal

import pytest
from django.urls import reverse

from apps.catalog.models import BundleItem
from factories import CategoryFactory, ProductFactory, UserFactory


@pytest.mark.django_db
class TestProductModel:
    def test_slug_auto_generated_and_unique(self):
        p1 = ProductFactory(name="Great Book", slug="")
        p2 = ProductFactory(name="Great Book", slug="")
        assert p1.slug == "great-book"
        assert p2.slug == "great-book-1"

    def test_discount_percent(self):
        product = ProductFactory(price=Decimal("80.00"), compare_at_price=Decimal("100.00"))
        assert product.discount_percent == 20

    def test_simple_product_in_stock(self):
        product = ProductFactory(is_bundle=False, stock=5)
        assert product.in_stock is True
        assert product.available_stock == 5

    def test_simple_product_out_of_stock(self):
        product = ProductFactory(is_bundle=False, stock=0)
        assert product.in_stock is False

    def test_bundle_stock_derived_from_books(self):
        book_a = ProductFactory(stock=10)
        book_b = ProductFactory(stock=3)
        bundle = ProductFactory(is_bundle=True, stock=999)  # stock field should be ignored
        BundleItem.objects.create(bundle=bundle, book=book_a, quantity=1)
        BundleItem.objects.create(bundle=bundle, book=book_b, quantity=1)
        assert bundle.available_stock == 3  # limited by the scarcer book

    def test_bundle_stock_respects_quantity_per_item(self):
        book = ProductFactory(stock=10)
        bundle = ProductFactory(is_bundle=True)
        BundleItem.objects.create(bundle=bundle, book=book, quantity=2)
        assert bundle.available_stock == 5

    def test_bundle_with_no_items_has_zero_stock(self):
        bundle = ProductFactory(is_bundle=True, stock=50)
        assert bundle.available_stock == 0
        assert bundle.in_stock is False

    def test_deduct_stock_on_simple_product(self):
        product = ProductFactory(stock=10)
        product.deduct_stock(3)
        product.refresh_from_db()
        assert product.stock == 7

    def test_deduct_stock_on_bundle_deducts_each_book(self):
        book_a = ProductFactory(stock=10)
        book_b = ProductFactory(stock=10)
        bundle = ProductFactory(is_bundle=True)
        BundleItem.objects.create(bundle=bundle, book=book_a, quantity=1)
        BundleItem.objects.create(bundle=bundle, book=book_b, quantity=2)
        bundle.deduct_stock(1)
        book_a.refresh_from_db()
        book_b.refresh_from_db()
        assert book_a.stock == 9
        assert book_b.stock == 8

    def test_restock_reverses_deduction(self):
        product = ProductFactory(stock=10)
        product.deduct_stock(4)
        product.restock(4)
        product.refresh_from_db()
        assert product.stock == 10


@pytest.mark.django_db
class TestCategoryModel:
    def test_slug_collision_is_handled(self):
        c1 = CategoryFactory(name="C", slug="")
        c2 = CategoryFactory(name="C++", slug="")
        assert c1.slug != c2.slug

    def test_parent_child_relationship(self):
        parent = CategoryFactory(name="DSA")
        child = CategoryFactory(name="DSA with Python", parent=parent)
        assert child in parent.children.all()


@pytest.mark.django_db
class TestCatalogViews:
    def test_product_list_shows_active_products(self, client):
        ProductFactory(name="Visible Product", is_active=True)
        ProductFactory(name="Hidden Product", is_active=False)
        response = client.get(reverse("catalog:product_list"))
        assert response.status_code == 200
        assert b"Visible Product" in response.content
        assert b"Hidden Product" not in response.content

    def test_product_list_search(self, client):
        ProductFactory(name="Django for Beginners")
        ProductFactory(name="Unrelated Widget")
        response = client.get(reverse("catalog:product_list"), {"q": "Django"})
        assert b"Django for Beginners" in response.content
        assert b"Unrelated Widget" not in response.content

    def test_category_detail_filters_by_category(self, client):
        cat_a = CategoryFactory(name="Books")
        cat_b = CategoryFactory(name="Merch")
        ProductFactory(name="Book Product", category=cat_a)
        ProductFactory(name="Merch Product", category=cat_b)
        response = client.get(reverse("catalog:category_detail", kwargs={"slug": cat_a.slug}))
        assert b"Book Product" in response.content
        assert b"Merch Product" not in response.content

    def test_product_detail_200(self, client):
        product = ProductFactory()
        response = client.get(product.get_absolute_url())
        assert response.status_code == 200
        assert product.name.encode() in response.content

    def test_product_detail_404_for_inactive(self, client):
        product = ProductFactory(is_active=False)
        response = client.get(product.get_absolute_url())
        assert response.status_code == 404

    def test_product_detail_shows_bundle_contents(self, client):
        book = ProductFactory(name="Solo Book")
        bundle = ProductFactory(name="Combo Bundle", is_bundle=True)
        BundleItem.objects.create(bundle=bundle, book=book, quantity=1)
        response = client.get(bundle.get_absolute_url())
        assert b"Solo Book" in response.content

    def test_submit_review_requires_login(self, client):
        product = ProductFactory()
        response = client.post(reverse("catalog:submit_review", kwargs={"slug": product.slug}))
        assert response.status_code == 302
        assert "/accounts/login/" in response.url

    def test_submit_review_authenticated(self, client):
        user = UserFactory()
        product = ProductFactory()
        client.force_login(user)
        response = client.post(
            reverse("catalog:submit_review", kwargs={"slug": product.slug}),
            {"rating": 5, "title": "Loved it", "body": "Great book overall."},
        )
        assert response.status_code == 302
        assert product.reviews.filter(user=user, rating=5).exists()

    def test_cannot_review_same_product_twice(self, client):
        user = UserFactory()
        product = ProductFactory()
        product.reviews.create(user=user, rating=4, title="First", body="ok")
        client.force_login(user)
        response = client.post(
            reverse("catalog:submit_review", kwargs={"slug": product.slug}),
            {"rating": 5, "title": "Second", "body": "ok"},
        )
        assert response.status_code == 302
        assert product.reviews.filter(user=user).count() == 1
