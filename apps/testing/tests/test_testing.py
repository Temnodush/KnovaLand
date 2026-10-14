import pytest

from apps.courses.models import Course, Section
from apps.materials.models import Material
from apps.testing.models import Choice, Question, Test

pytestmark = pytest.mark.django_db


@pytest.fixture
def material(teacher_user):
    course = Course.objects.create(title="Python", owner=teacher_user)
    section = Section.objects.create(course=course, title="Basics")
    return Material.objects.create(section=section, title="Variables", owner=teacher_user)


@pytest.fixture
def test_obj(teacher_user, material):
    """Тест с одним вопросом и двумя вариантами (1 правильный)."""
    test = Test.objects.create(
        material=material, title="Quiz", owner=teacher_user, passing_score=60
    )
    q = Question.objects.create(test=test, text="2+2?", order=1)
    Choice.objects.create(question=q, text="4", is_correct=True)
    Choice.objects.create(question=q, text="5", is_correct=False)
    return test


def test_teacher_creates_test_with_questions(teacher_client, material):
    payload = {
        "material": material.id,
        "title": "New test",
        "passing_score": 50,
        "questions": [
            {
                "text": "Capital of France?",
                "order": 1,
                "choices": [
                    {"text": "Paris", "is_correct": True},
                    {"text": "Rome", "is_correct": False},
                ],
            }
        ],
    }
    response = teacher_client.post("/api/tests/", payload, format="json")
    assert response.status_code == 201
    assert response.data["questions"][0]["choices"][0]["text"] == "Paris"
    assert Test.objects.count() == 1


def test_teacher_cannot_add_test_to_foreign_material(other_teacher_client, material):
    payload = {"material": material.id, "title": "X", "questions": []}
    response = other_teacher_client.post("/api/tests/", payload, format="json")
    assert response.status_code == 400


def test_student_read_hides_correct_answers(student_client, test_obj):
    response = student_client.get(f"/api/tests/{test_obj.id}/")
    assert response.status_code == 200
    choices = response.data["questions"][0]["choices"]
    for choice in choices:
        assert "is_correct" not in choice


def test_teacher_read_shows_correct_answers(teacher_client, test_obj):
    response = teacher_client.get(f"/api/tests/{test_obj.id}/")
    assert response.status_code == 200
    choices = response.data["questions"][0]["choices"]
    assert any(c["is_correct"] for c in choices)


def test_submit_correct_passes(student_client, test_obj):
    question = test_obj.questions.first()
    correct = question.choices.get(is_correct=True)
    response = student_client.post(
        f"/api/tests/{test_obj.id}/submit/",
        {"answers": [{"question": question.id, "choices": [correct.id]}]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["score"] == 1
    assert response.data["total"] == 1
    assert response.data["percentage"] == 100.0
    assert response.data["is_passed"] is True


def test_submit_wrong_fails(student_client, test_obj):
    question = test_obj.questions.first()
    wrong = question.choices.get(is_correct=False)
    response = student_client.post(
        f"/api/tests/{test_obj.id}/submit/",
        {"answers": [{"question": question.id, "choices": [wrong.id]}]},
        format="json",
    )
    assert response.status_code == 201
    assert response.data["score"] == 0
    assert response.data["is_passed"] is False


def test_submit_requires_authentication(api_client, test_obj):
    question = test_obj.questions.first()
    response = api_client.post(
        f"/api/tests/{test_obj.id}/submit/",
        {"answers": [{"question": question.id, "choices": []}]},
        format="json",
    )
    assert response.status_code == 401


def test_teacher_cannot_submit(teacher_client, test_obj):
    question = test_obj.questions.first()
    response = teacher_client.post(
        f"/api/tests/{test_obj.id}/submit/",
        {"answers": [{"question": question.id, "choices": []}]},
        format="json",
    )
    assert response.status_code == 403


def test_submit_missing_answers(student_client, test_obj):
    response = student_client.post(
        f"/api/tests/{test_obj.id}/submit/", {"answers": []}, format="json"
    )
    assert response.status_code == 400


def test_my_results(student_client, test_obj):
    question = test_obj.questions.first()
    correct = question.choices.get(is_correct=True)
    student_client.post(
        f"/api/tests/{test_obj.id}/submit/",
        {"answers": [{"question": question.id, "choices": [correct.id]}]},
        format="json",
    )
    response = student_client.get("/api/tests/my-results/")
    assert response.status_code == 200
    assert response.data[0]["is_passed"] is True


def test_results_owner_only(teacher_client, other_teacher_client, test_obj):
    assert teacher_client.get(f"/api/tests/{test_obj.id}/results/").status_code == 200
    assert other_teacher_client.get(f"/api/tests/{test_obj.id}/results/").status_code == 403
