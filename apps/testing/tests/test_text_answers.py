import pytest

from apps.courses.models import Course, Section
from apps.materials.models import Material
from apps.testing.models import Question, Test

pytestmark = pytest.mark.django_db


@pytest.fixture
def text_test(teacher_user):
    course = Course.objects.create(title="Py", owner=teacher_user, is_published=True)
    section = Section.objects.create(course=course, title="S1", order=1)
    material = Material.objects.create(section=section, title="M1", owner=teacher_user)
    test = Test.objects.create(material=material, title="T", owner=teacher_user, passing_score=60)
    question = Question.objects.create(
        test=test, text="Имя функции вывода?", kind=Question.Kind.TEXT, answer_text="print", order=1
    )
    return {"test": test, "question": question}


def _submit(client, test, payload):
    return client.post(f"/api/tests/{test.id}/submit/", {"answers": [payload]}, format="json")


def test_text_answer_correct(student_client, text_test):
    question = text_test["question"]
    response = _submit(
        student_client, text_test["test"], {"question": question.id, "text": "print"}
    )
    assert response.status_code == 201
    assert response.data["score"] == 1
    assert response.data["is_passed"] is True


def test_text_answer_trim_and_case_insensitive(student_client, text_test):
    question = text_test["question"]
    response = _submit(
        student_client, text_test["test"], {"question": question.id, "text": "  PRINT  "}
    )
    assert response.status_code == 201
    assert response.data["score"] == 1


def test_text_answer_wrong(student_client, text_test):
    question = text_test["question"]
    response = _submit(
        student_client, text_test["test"], {"question": question.id, "text": "input"}
    )
    assert response.status_code == 201
    assert response.data["score"] == 0
    assert response.data["is_passed"] is False


def test_text_question_hides_answer_from_student(student_client, text_test):
    response = student_client.get(f"/api/tests/{text_test['test'].id}/")
    question = response.data["questions"][0]
    assert question["kind"] == "text"
    assert "answer_text" not in question


def test_teacher_can_read_answer(teacher_client, text_test):
    response = teacher_client.get(f"/api/tests/{text_test['test'].id}/")
    question = response.data["questions"][0]
    assert question["answer_text"] == "print"


def test_teacher_creates_text_question(teacher_client, teacher_user):
    course = Course.objects.create(title="Py2", owner=teacher_user)
    section = Section.objects.create(course=course, title="S")
    material = Material.objects.create(section=section, title="M", owner=teacher_user)
    payload = {
        "material": material.id,
        "title": "Text test",
        "questions": [
            {"text": "Сколько будет 2+2?", "kind": "text", "answer_text": "4", "order": 1}
        ],
    }
    response = teacher_client.post("/api/tests/", payload, format="json")
    assert response.status_code == 201
    assert response.data["questions"][0]["kind"] == "text"
    assert response.data["questions"][0]["answer_text"] == "4"


def test_teacher_text_question_requires_answer(teacher_client, teacher_user):
    course = Course.objects.create(title="Py3", owner=teacher_user)
    section = Section.objects.create(course=course, title="S")
    material = Material.objects.create(section=section, title="M", owner=teacher_user)
    payload = {
        "material": material.id,
        "title": "Bad",
        "questions": [{"text": "?", "kind": "text", "answer_text": "", "order": 1}],
    }
    response = teacher_client.post("/api/tests/", payload, format="json")
    assert response.status_code == 400


def test_multiple_accepted_answers(student_client, teacher_user):
    course = Course.objects.create(title="Py4", owner=teacher_user)
    section = Section.objects.create(course=course, title="S")
    material = Material.objects.create(section=section, title="M", owner=teacher_user)
    test = Test.objects.create(material=material, title="T", owner=teacher_user)
    question = Question.objects.create(
        test=test, text="?", kind=Question.Kind.TEXT, answer_text="да|yes", order=1
    )
    response = _submit(student_client, test, {"question": question.id, "text": "YES"})
    assert response.data["score"] == 1
