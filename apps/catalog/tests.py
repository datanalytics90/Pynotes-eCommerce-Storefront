from decimal import Decimal

import pytest
from django.urls import reverse

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

    def test_in_stock_digital_always_true(self):
        product = ProductFactory(is_digital=True, stock=0)
        assert product.in_stock is True

    def test_in_stock_physical_depends_on_stock(self):
        product = ProductFactory(is_digital=False, stock=0)
        assert product.in_stock is False


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
            {"rating": 5, "title": "Loved it", "body": "Great product overall."},
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
