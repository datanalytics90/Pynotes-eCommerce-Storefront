import pytest
from django.urls import reverse

from apps.core.models import ContactMessage
from factories import ProductFactory


@pytest.mark.django_db
class TestCoreViews:
    def test_home_page_loads(self, client):
        response = client.get(reverse("core:home"))
        assert response.status_code == 200

    def test_home_shows_featured_products(self, client):
        ProductFactory(name="Featured Thing", is_featured=True)
        response = client.get(reverse("core:home"))
        assert b"Featured Thing" in response.content

    def test_about_page_loads(self, client):
        response = client.get(reverse("core:about"))
        assert response.status_code == 200

    def test_contact_form_submission_saves_message(self, client):
        response = client.post(
            reverse("core:contact"),
            {
                "name": "Jane",
                "email": "jane@example.com",
                "subject": "Question about an order",
                "message": "Hello, I have a question.",
            },
        )
        assert response.status_code == 302
        assert ContactMessage.objects.filter(email="jane@example.com").exists()
