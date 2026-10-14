import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.urls import reverse

from apps.courses.models import Course

User = get_user_model()
pytestmark = pytest.mark.django_db

PASSWORD = "Knova-Strong-123"


@pytest.fixture
def teacher_staff(db):
    return User.objects.create_user(
        username="teach",
        email="teach@example.com",
        password=PASSWORD,
        role=User.Role.TEACHER,
        is_staff=True,
    )


@pytest.fixture
def other_teacher_staff(db):
    return User.objects.create_user(
        username="teach2",
        email="teach2@example.com",
        password=PASSWORD,
        role=User.Role.TEACHER,
        is_staff=True,
    )


def _client(user):
    client = Client()
    client.force_login(user)
    return client


def test_teacher_can_access_admin(teacher_staff):
    response = _client(teacher_staff).get(reverse("admin:index"))
    assert response.status_code == 200


def test_non_staff_cannot_access_admin(student_user):
    response = _client(student_user).get(reverse("admin:index"))
    assert response.status_code == 302
    assert "/admin/login/" in response.url


def test_teacher_registration_gets_staff_access(client):
    from apps.users.forms import WebRegisterForm

    assert WebRegisterForm is not None
    User.objects.create_user(
        username="t3",
        email="t3@example.com",
        password=PASSWORD,
        role=User.Role.TEACHER,
        is_staff=True,
    )
    # Проверяем, что форма регистрации преподавателя делает его сотрудником.
    form = WebRegisterForm(
        data={
            "username": "teachform",
            "email": "teachform@example.com",
            "password1": PASSWORD,
            "password2": PASSWORD,
            "role": User.Role.TEACHER,
        }
    )
    assert form.is_valid(), form.errors
    user = form.save()
    assert user.is_staff is True


def test_teacher_sees_only_own_courses(teacher_staff, other_teacher_staff):
    mine = Course.objects.create(title="MyCourse", owner=teacher_staff)
    foreign = Course.objects.create(title="ForeignCourse", owner=other_teacher_staff)
    response = _client(teacher_staff).get(reverse("admin:courses_course_changelist"))
    body = response.content.decode()
    assert mine.title in body
    assert foreign.title not in body


def test_teacher_can_add_course_via_admin(teacher_staff):
    data = {
        "title": "AdminMade",
        "description": "created via admin",
        "is_published": "on",
        "price": "0",
        "icon": "📘",
        "sections-TOTAL_FORMS": "0",
        "sections-INITIAL_FORMS": "0",
        "sections-MIN_NUM_FORMS": "0",
        "sections-MAX_NUM_FORMS": "1000",
    }
    response = _client(teacher_staff).post(reverse("admin:courses_course_add"), data)
    assert response.status_code == 302
    course = Course.objects.get(title="AdminMade")
    assert course.owner == teacher_staff


def test_teacher_cannot_open_foreign_course(teacher_staff, other_teacher_staff):
    foreign = Course.objects.create(title="Foreign", owner=other_teacher_staff)
    url = reverse("admin:courses_course_change", args=[foreign.id])
    response = _client(teacher_staff).get(url)
    # Чужой объект недоступен: админка перенаправляет (302) или запрещает (403/404).
    assert response.status_code in (302, 403, 404)


def test_teacher_cannot_see_users_module(teacher_staff):
    assert _client(teacher_staff).get(reverse("admin:users_user_changelist")).status_code == 403


def test_admin_login_page_anonymous_does_not_crash(client):
    # Регресс: на логине пользователь анонимный (нет свойства is_teacher).
    response = client.get(reverse("admin:login"))
    assert response.status_code == 200


def test_admin_index_anonymous_redirects_to_login(client):
    response = client.get(reverse("admin:index"))
    assert response.status_code == 302
    assert "/admin/login/" in response.url
