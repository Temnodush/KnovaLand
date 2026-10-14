import pytest
from django.test import Client

from apps.courses.models import Course, Section
from apps.gamification.models import Enrollment, MaterialProgress
from apps.materials.models import Material

pytestmark = pytest.mark.django_db


@pytest.fixture
def course(teacher_user):
    course = Course.objects.create(title="Python", owner=teacher_user, is_published=True)
    section = Section.objects.create(course=course, title="Basics")
    Material.objects.create(section=section, title="M1", owner=teacher_user)
    return course


def _client(user):
    client = Client()
    client.force_login(user)
    return client


def test_home_shows_courses(client, course):
    response = client.get("/")
    assert response.status_code == 200
    assert "Python" in response.content.decode()


def test_login_page(client):
    assert client.get("/login/").status_code == 200


def test_dashboard_requires_login(client):
    response = client.get("/dashboard/")
    assert response.status_code == 302
    assert "/login/" in response.url


def test_dashboard_authenticated(student_user):
    response = _client(student_user).get("/dashboard/")
    assert response.status_code == 200


def test_course_detail_authenticated(student_user, course):
    response = _client(student_user).get(f"/courses/{course.id}/")
    assert response.status_code == 200
    assert "M1" in response.content.decode()


def test_enroll_course(student_user, course):
    client = _client(student_user)
    response = client.post(f"/courses/{course.id}/enroll/")
    assert response.status_code == 302
    assert Enrollment.objects.filter(user=student_user, course=course).exists()


def test_complete_material_htmx(student_user, course):
    material = Material.objects.filter(section__course=course).first()
    client = _client(student_user)
    response = client.post(f"/materials/{material.id}/complete/", HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    assert "+10 XP" in response.content.decode()
    assert MaterialProgress.objects.filter(user=student_user, material=material).exists()


def test_complete_material_redirect(student_user, course):
    material = Material.objects.filter(section__course=course).first()
    response = _client(student_user).post(f"/materials/{material.id}/complete/")
    assert response.status_code == 302


def test_leaderboard_and_profile(student_user):
    client = _client(student_user)
    assert client.get("/leaderboard/").status_code == 200
    assert client.get("/profile/").status_code == 200
