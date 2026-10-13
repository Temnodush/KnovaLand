import pytest
from rest_framework.test import APIClient

from apps.users.models import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="pass12345",
        role=User.Role.ADMIN,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def teacher_user(db):
    return User.objects.create_user(
        username="teacher",
        email="teacher@example.com",
        password="pass12345",
        role=User.Role.TEACHER,
    )


@pytest.fixture
def other_teacher(db):
    return User.objects.create_user(
        username="teacher2",
        email="teacher2@example.com",
        password="pass12345",
        role=User.Role.TEACHER,
    )


@pytest.fixture
def student_user(db):
    return User.objects.create_user(
        username="student",
        email="student@example.com",
        password="pass12345",
        role=User.Role.STUDENT,
    )


def _auth_client(user):
    """Клиент с реальным JWT-токеном для пользователя."""
    client = APIClient()
    response = client.post(
        "/api/auth/token/",
        {"email": user.email, "password": "pass12345"},
        format="json",
    )
    assert response.status_code == 200, response.content
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.data['access']}")
    return client


@pytest.fixture
def admin_client(admin_user):
    return _auth_client(admin_user)


@pytest.fixture
def teacher_client(teacher_user):
    return _auth_client(teacher_user)


@pytest.fixture
def other_teacher_client(other_teacher):
    return _auth_client(other_teacher)


@pytest.fixture
def student_client(student_user):
    return _auth_client(student_user)
