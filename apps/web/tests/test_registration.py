import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse

from apps.users.tokens import (
    make_email_verification_token,
    read_email_verification_token,
)

User = get_user_model()
pytestmark = pytest.mark.django_db

STRONG_PASSWORD = "Knova-Strong-123"


def test_register_page_renders(client):
    response = client.get(reverse("web:register"))
    assert response.status_code == 200
    assert "Регистрация" in response.content.decode()


def test_register_creates_user_and_sends_email(client, mailoutbox):
    response = client.post(
        reverse("web:register"),
        {
            "username": "newuser",
            "email": "newuser@example.com",
            "password1": STRONG_PASSWORD,
            "password2": STRONG_PASSWORD,
            "role": User.Role.STUDENT,
        },
    )
    assert response.status_code == 302
    user = User.objects.get(username="newuser")
    assert user.email_verified is False
    assert user.role == User.Role.STUDENT
    assert len(mailoutbox) == 1
    assert "newuser@example.com" in mailoutbox[0].to
    assert "/verify-email/" in mailoutbox[0].body


def test_register_duplicate_email(client):
    User.objects.create_user(username="exists", email="dup@example.com", password=STRONG_PASSWORD)
    response = client.post(
        reverse("web:register"),
        {
            "username": "another",
            "email": "dup@example.com",
            "password1": STRONG_PASSWORD,
            "password2": STRONG_PASSWORD,
            "role": User.Role.STUDENT,
        },
    )
    assert response.status_code == 200
    assert User.objects.filter(username="another").count() == 0
    assert "уже существует" in response.content.decode()


def test_register_password_mismatch(client):
    response = client.post(
        reverse("web:register"),
        {
            "username": "mismatch",
            "email": "mismatch@example.com",
            "password1": STRONG_PASSWORD,
            "password2": "Other-123-xyz",
            "role": User.Role.STUDENT,
        },
    )
    assert response.status_code == 200
    assert not User.objects.filter(username="mismatch").exists()


def test_verify_email_valid_token(client, student_user):
    assert student_user.email_verified is False
    token = make_email_verification_token(student_user)
    response = client.get(reverse("web:verify-email", kwargs={"token": token}))
    assert response.status_code == 302
    student_user.refresh_from_db()
    assert student_user.email_verified is True


def test_verify_email_invalid_token(client):
    response = client.get(reverse("web:verify-email", kwargs={"token": "garbage-token"}))
    assert response.status_code == 302


def test_resend_verification_requires_login(client):
    response = client.post(reverse("web:resend-verification"))
    assert response.status_code == 302
    assert "/login/" in response.url


def test_resend_verification_sends_email(client, student_user, mailoutbox):
    client.force_login(student_user)
    response = client.post(reverse("web:resend-verification"))
    assert response.status_code == 302
    assert len(mailoutbox) == 1


def test_token_roundtrip(student_user):
    token = make_email_verification_token(student_user)
    assert read_email_verification_token(token) == student_user.pk


def test_token_rejects_garbage():
    assert read_email_verification_token("not-a-real-token") is None


def test_login_by_username_after_verification(client, student_user):
    student_user.email_verified = True
    student_user.save(update_fields=["email_verified"])
    response = client.post(
        reverse("web:login"),
        {"username": "student", "password": "pass12345"},
    )
    assert response.status_code == 302


def test_api_register_sends_verification_email(api_client, mailoutbox):
    response = api_client.post(
        "/api/auth/register/",
        {
            "username": "apiuser",
            "email": "apiuser@example.com",
            "password": STRONG_PASSWORD,
            "password2": STRONG_PASSWORD,
        },
        format="json",
    )
    assert response.status_code == 201
    assert response.data["email_verified"] is False
    assert len(mailoutbox) == 1
    assert "apiuser@example.com" in mailoutbox[0].to
