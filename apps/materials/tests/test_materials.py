import pytest

from apps.courses.models import Course, Section
from apps.materials.models import Material

pytestmark = pytest.mark.django_db


@pytest.fixture
def section(teacher_user):
    course = Course.objects.create(title="Python", owner=teacher_user)
    return Section.objects.create(course=course, title="Basics")


def test_teacher_creates_material(teacher_client, section, teacher_user):
    response = teacher_client.post(
        "/api/materials/",
        {"section": section.id, "title": "Variables", "content": "text"},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["owner"] == teacher_user.id


def test_other_teacher_cannot_add_material(other_teacher_client, section):
    response = other_teacher_client.post(
        "/api/materials/", {"section": section.id, "title": "X"}, format="json"
    )
    assert response.status_code == 400


def test_owner_updates_material(teacher_client, section, teacher_user):
    material = Material.objects.create(section=section, title="Old", owner=teacher_user)
    response = teacher_client.patch(
        f"/api/materials/{material.id}/", {"title": "New"}, format="json"
    )
    assert response.status_code == 200
    material.refresh_from_db()
    assert material.title == "New"


def test_other_teacher_cannot_update_material(other_teacher_client, section, teacher_user):
    material = Material.objects.create(section=section, title="Old", owner=teacher_user)
    response = other_teacher_client.patch(
        f"/api/materials/{material.id}/", {"title": "New"}, format="json"
    )
    assert response.status_code == 403


def test_student_can_read_materials(student_client, section, teacher_user):
    Material.objects.create(section=section, title="Read me", owner=teacher_user)
    response = student_client.get("/api/materials/")
    assert response.status_code == 200
    assert response.data["count"] == 1


def test_student_cannot_create_material(student_client, section):
    response = student_client.post(
        "/api/materials/", {"section": section.id, "title": "X"}, format="json"
    )
    assert response.status_code == 403
