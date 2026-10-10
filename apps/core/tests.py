import pytest
from django.urls import reverse

from apps.core.models import FAQ, ContactMessage, LegalPage
from factories import ProductFactory


@pytest.mark.django_db
class TestCoreViews:
    def test_home_page_loads(self, client):
        response = client.get(reverse("core:home"))
        assert response.status_code == 200

    def test_home_shows_featured_products(self, client):
        ProductFactory(name="Featured Thing", is_featured=True, is_bundle=False)
        response = client.get(reverse("core:home"))
        assert b"Featured Thing" in response.content

    def test_home_shows_bundles_table(self, client):
        ProductFactory(name="Combo Bundle", is_bundle=True)
        response = client.get(reverse("core:home"))
        assert b"Combo Bundle" in response.content

    def test_faq_page_groups_by_category(self, client):
        FAQ.objects.create(question="Do you ship PDFs?", answer="No, printed only.", group=FAQ.Group.ORDERING)
        response = client.get(reverse("core:faq"))
        assert response.status_code == 200
        assert b"Do you ship PDFs?" in response.content

    def test_legal_page_renders(self, client):
        LegalPage.objects.create(slug="privacy", title="Privacy Policy", body="We respect your data.")
        response = client.get(reverse("core:legal_page", kwargs={"slug": "privacy"}))
        assert response.status_code == 200
        assert b"We respect your data." in response.content

    def test_legal_page_404_when_missing(self, client):
        response = client.get(reverse("core:legal_page", kwargs={"slug": "privacy"}))
        assert response.status_code == 404

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
