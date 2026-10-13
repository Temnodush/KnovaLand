import pytest

from apps.courses.models import Course, Section

pytestmark = pytest.mark.django_db


@pytest.fixture
def course(teacher_user):
    return Course.objects.create(title="Python", description="d", owner=teacher_user)


def test_teacher_creates_course(teacher_client, teacher_user):
    response = teacher_client.post(
        "/api/courses/", {"title": "Django", "description": "x"}, format="json"
    )
    assert response.status_code == 201
    assert response.data["owner"] == teacher_user.id
    assert Course.objects.filter(title="Django", owner=teacher_user).exists()


def test_student_cannot_create_course(student_client):
    response = student_client.post("/api/courses/", {"title": "X"}, format="json")
    assert response.status_code == 403


def test_teacher_cannot_edit_foreign_course(other_teacher_client, course):
    response = other_teacher_client.patch(
        f"/api/courses/{course.id}/", {"title": "Hacked"}, format="json"
    )
    assert response.status_code == 403


def test_owner_can_update_course(teacher_client, course):
    response = teacher_client.patch(
        f"/api/courses/{course.id}/", {"title": "Python 3"}, format="json"
    )
    assert response.status_code == 200
    course.refresh_from_db()
    assert course.title == "Python 3"


def test_admin_can_update_any_course(admin_client, course):
    response = admin_client.patch(
        f"/api/courses/{course.id}/", {"title": "Admin edit"}, format="json"
    )
    assert response.status_code == 200


def test_owner_can_delete_course(teacher_client, course):
    response = teacher_client.delete(f"/api/courses/{course.id}/")
    assert response.status_code == 204
    assert not Course.objects.filter(id=course.id).exists()


def test_student_sees_only_published(teacher_user, student_client):
    Course.objects.create(title="Hidden", owner=teacher_user, is_published=False)
    Course.objects.create(title="Visible", owner=teacher_user, is_published=True)
    response = student_client.get("/api/courses/")
    assert response.status_code == 200
    titles = [c["title"] for c in response.data["results"]]
    assert "Visible" in titles
    assert "Hidden" not in titles


def test_sections_nested_in_course_detail(teacher_client, course):
    Section.objects.create(course=course, title="Intro", order=1)
    response = teacher_client.get(f"/api/courses/{course.id}/")
    assert response.status_code == 200
    assert len(response.data["sections"]) == 1
    assert response.data["sections"][0]["title"] == "Intro"


def test_teacher_creates_section_in_own_course(teacher_client, course):
    response = teacher_client.post(
        "/api/sections/", {"course": course.id, "title": "S1"}, format="json"
    )
    assert response.status_code == 201


def test_other_teacher_cannot_add_section(other_teacher_client, course):
    response = other_teacher_client.post(
        "/api/sections/", {"course": course.id, "title": "S1"}, format="json"
    )
    assert response.status_code == 400
