import pytest
from django.urls import reverse

from apps.accounts.models import Address, User
from factories import AddressFactory, UserFactory


@pytest.mark.django_db
class TestUserModel:
    def test_create_user_normalizes_email_domain(self):
        user = User.objects.create_user(email="Test@Example.COM", password="pass12345")
        assert user.email == "Test@example.com"
        assert user.check_password("pass12345")

    def test_create_user_requires_email(self):
        with pytest.raises(ValueError):
            User.objects.create_user(email="", password="pass12345")

    def test_create_superuser_sets_flags(self):
        admin = User.objects.create_superuser(email="admin@example.com", password="pass12345")
        assert admin.is_staff and admin.is_superuser

    def test_only_one_default_address_per_type(self):
        user = UserFactory()
        addr1 = AddressFactory(user=user, is_default=True)
        addr2 = AddressFactory(user=user, is_default=True)
        addr1.refresh_from_db()
        assert addr1.is_default is False
        assert addr2.is_default is True


@pytest.mark.django_db
class TestAuthViews:
    def test_signup_creates_user_and_logs_in(self, client):
        response = client.post(
            reverse("accounts:signup"),
            {
                "email": "new@example.com",
                "first_name": "New",
                "last_name": "User",
                "password1": "SuperSecret123!",
                "password2": "SuperSecret123!",
            },
        )
        assert response.status_code == 302
        assert User.objects.filter(email="new@example.com").exists()
        assert response.wsgi_request.user.is_authenticated

    def test_login_with_email(self, client):
        UserFactory(email="login@example.com", password="pass12345")
        response = client.post(
            reverse("accounts:login"), {"username": "login@example.com", "password": "pass12345"}
        )
        assert response.status_code == 302

    def test_login_wrong_password_fails(self, client):
        UserFactory(email="login2@example.com", password="pass12345")
        response = client.post(
            reverse("accounts:login"), {"username": "login2@example.com", "password": "wrong"}
        )
        assert response.status_code == 200
        assert not response.wsgi_request.user.is_authenticated

    def test_profile_requires_login(self, client):
        response = client.get(reverse("accounts:profile"))
        assert response.status_code == 302

    def test_profile_update(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(
            reverse("accounts:profile"),
            {"first_name": "Updated", "last_name": "Name", "phone_number": "", "newsletter_opt_in": ""},
        )
        assert response.status_code == 302
        user.refresh_from_db()
        assert user.first_name == "Updated"

    def test_address_create(self, client):
        user = UserFactory()
        client.force_login(user)
        response = client.post(
            reverse("accounts:address_create"),
            {
                "address_type": "shipping",
                "full_name": "Jane Doe",
                "line1": "1 Infinite Loop",
                "line2": "",
                "city": "Cupertino",
                "state": "CA",
                "postal_code": "95014",
                "country": "United States",
                "phone_number": "",
                "is_default": "on",
            },
        )
        assert response.status_code == 302
        assert Address.objects.filter(user=user, city="Cupertino").exists()

    def test_address_delete_only_own(self, client):
        owner = UserFactory()
        other = UserFactory()
        address = AddressFactory(user=owner)
        client.force_login(other)
        response = client.post(reverse("accounts:address_delete", kwargs={"pk": address.pk}))
        assert response.status_code == 404
        assert Address.objects.filter(pk=address.pk).exists()
