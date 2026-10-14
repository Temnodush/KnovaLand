import pytest

from apps.users.models import User

pytestmark = pytest.mark.django_db


def test_register_success(api_client):
    payload = {
        "username": "newbie",
        "email": "newbie@example.com",
        "password": "strongpass123",
        "password2": "strongpass123",
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 201
    assert response.data["email"] == "newbie@example.com"
    assert response.data["role"] == User.Role.STUDENT
    assert User.objects.filter(email="newbie@example.com").exists()


def test_register_password_mismatch(api_client):
    payload = {
        "username": "newbie",
        "email": "newbie@example.com",
        "password": "strongpass123",
        "password2": "different123",
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 400
    assert "password2" in response.data


def test_register_duplicate_email(api_client, student_user):
    payload = {
        "username": "dup",
        "email": student_user.email,
        "password": "strongpass123",
        "password2": "strongpass123",
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 400
    assert "email" in response.data


def test_register_cannot_choose_admin(api_client):
    payload = {
        "username": "hacker",
        "email": "hacker@example.com",
        "password": "strongpass123",
        "password2": "strongpass123",
        "role": "admin",
    }
    response = api_client.post("/api/auth/register/", payload, format="json")
    assert response.status_code == 400
    assert "role" in response.data


def test_login_returns_jwt(api_client, student_user):
    response = api_client.post(
        "/api/auth/token/",
        {"email": student_user.email, "password": "pass12345"},
        format="json",
    )
    assert response.status_code == 200
    assert "access" in response.data
    assert "refresh" in response.data


def test_login_wrong_password(api_client, student_user):
    response = api_client.post(
        "/api/auth/token/",
        {"email": student_user.email, "password": "wrong"},
        format="json",
    )
    assert response.status_code == 401


def test_protected_endpoint_requires_token(api_client):
    response = api_client.get("/api/users/me/")
    assert response.status_code == 401


def test_me_endpoint(student_client, student_user):
    response = student_client.get("/api/users/me/")
    assert response.status_code == 200
    assert response.data["email"] == student_user.email


def test_users_list_admin_only(admin_client, student_client, student_user):
    assert admin_client.get("/api/users/").status_code == 200
    assert student_client.get("/api/users/").status_code == 403


def test_session_login_by_username(student_user):
    from django.test import Client

    assert Client().login(username="student", password="pass12345") is True


def test_session_login_by_email(student_user):
    from django.test import Client

    assert Client().login(username=student_user.email, password="pass12345") is True


def test_session_login_wrong_password(student_user):
    from django.test import Client

    assert Client().login(username="student", password="nope") is False
