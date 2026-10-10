import pytest
from django.urls import reverse
from rest_framework import status

from apps.accounts.models import User
from factories import CategoryFactory, ProductFactory, UserFactory


@pytest.mark.django_db
class TestProductApi:
    def test_list_only_active_products(self, api_client):
        ProductFactory(name="Active", is_active=True)
        ProductFactory(name="Inactive", is_active=False)
        response = api_client.get(reverse("api:product-list"))
        assert response.status_code == status.HTTP_200_OK
        names = [p["name"] for p in response.data["results"]]
        assert "Active" in names
        assert "Inactive" not in names

    def test_filter_by_category_slug(self, api_client):
        cat = CategoryFactory()
        ProductFactory(category=cat)
        other = ProductFactory()
        response = api_client.get(reverse("api:product-list"), {"category__slug": cat.slug})
        assert response.data["count"] == 1
        assert other.name not in [p["name"] for p in response.data["results"]]

    def test_retrieve_includes_description(self, api_client):
        product = ProductFactory()
        response = api_client.get(reverse("api:product-detail", kwargs={"slug": product.slug}))
        assert response.status_code == status.HTTP_200_OK
        assert response.data["description"] == product.description


@pytest.mark.django_db
class TestAuthApi:
    def test_register_creates_user(self, api_client):
        response = api_client.post(
            reverse("api:register"),
            {"email": "api@example.com", "first_name": "A", "last_name": "B", "password": "pass12345"},
        )
        assert response.status_code == status.HTTP_201_CREATED
        assert User.objects.filter(email="api@example.com").exists()

    def test_token_obtain_and_use(self, api_client):
        UserFactory(email="tok@example.com", password="pass12345")
        response = api_client.post(
            reverse("api:token_obtain_pair"), {"email": "tok@example.com", "password": "pass12345"}
        )
        assert response.status_code == status.HTTP_200_OK
        access = response.data["access"]

        api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {access}")
        me_response = api_client.get(reverse("api:me"))
        assert me_response.status_code == status.HTTP_200_OK
        assert me_response.data["email"] == "tok@example.com"

    def test_me_requires_auth(self, api_client):
        response = api_client.get(reverse("api:me"))
        assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestCartApi:
    def test_add_item_and_fetch_cart(self, api_client):
        product = ProductFactory(price="12.50", stock=5)
        response = api_client.post(reverse("api:cart"), {"product_id": product.id, "quantity": 2})
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["total_items"] == 2

        get_response = api_client.get(reverse("api:cart"))
        assert get_response.data["subtotal"] == "25.00"
