import pytest
from django.test import Client
from django.urls import reverse

from apps.courses.models import Course, Section
from apps.gamification import services
from apps.gamification.models import MaterialProgress, SectionSkill, Skill
from apps.materials.models import Material
from apps.testing.models import Choice, Question, Test

pytestmark = pytest.mark.django_db


@pytest.fixture
def course_with_test(teacher_user):
    course = Course.objects.create(title="Py", owner=teacher_user, is_published=True)
    section = Section.objects.create(course=course, title="S1", order=1)
    skill = Skill.objects.create(code="basics", title="Базовые знания")
    SectionSkill.objects.create(section=section, skill=skill)

    lesson1 = Material.objects.create(section=section, title="L1", owner=teacher_user, order=1)
    lesson2 = Material.objects.create(section=section, title="L2", owner=teacher_user, order=2)

    test = Test.objects.create(material=lesson1, title="T1", owner=teacher_user, passing_score=60)
    question = Question.objects.create(test=test, text="print?", order=1)
    correct = Choice.objects.create(question=question, text="print()", is_correct=True)
    wrong = Choice.objects.create(question=question, text="echo()", is_correct=False)
    return {
        "course": course,
        "skill": skill,
        "lesson1": lesson1,
        "lesson2": lesson2,
        "test": test,
        "question": question,
        "correct": correct,
        "wrong": wrong,
    }


def _client(user):
    client = Client()
    client.force_login(user)
    return client


def test_locked_lesson_redirects(student_user, course_with_test):
    services.enroll(student_user, course_with_test["course"])
    response = _client(student_user).get(
        reverse("web:lesson-detail", kwargs={"pk": course_with_test["lesson2"].id})
    )
    assert response.status_code == 302
    assert (
        reverse("web:course-detail", kwargs={"pk": course_with_test["course"].id}) in response.url
    )


def test_unlocked_lesson_renders(student_user, course_with_test):
    services.enroll(student_user, course_with_test["course"])
    response = _client(student_user).get(
        reverse("web:lesson-detail", kwargs={"pk": course_with_test["lesson1"].id})
    )
    assert response.status_code == 200


def test_trainer_hides_correct_answers(student_user, course_with_test):
    services.enroll(student_user, course_with_test["course"])
    response = _client(student_user).get(
        reverse("web:trainer", kwargs={"pk": course_with_test["lesson1"].id})
    )
    body = response.content.decode()
    assert response.status_code == 200
    assert "is_correct" not in body


def test_trainer_pass_completes_lesson_and_grants_skill(student_user, course_with_test):
    services.enroll(student_user, course_with_test["course"])
    client = _client(student_user)
    response = client.post(
        reverse("web:trainer-submit", kwargs={"pk": course_with_test["lesson1"].id}),
        {f"q_{course_with_test['question'].id}": [course_with_test["correct"].id]},
    )
    assert response.status_code == 200
    assert MaterialProgress.objects.filter(
        user=student_user, material=course_with_test["lesson1"]
    ).exists()


def test_trainer_fail_does_not_complete(student_user, course_with_test):
    services.enroll(student_user, course_with_test["course"])
    client = _client(student_user)
    client.post(
        reverse("web:trainer-submit", kwargs={"pk": course_with_test["lesson1"].id}),
        {f"q_{course_with_test['question'].id}": [course_with_test["wrong"].id]},
    )
    assert not MaterialProgress.objects.filter(
        user=student_user, material=course_with_test["lesson1"]
    ).exists()


def test_lesson2_unlocks_after_lesson1(student_user, course_with_test):
    services.enroll(student_user, course_with_test["course"])
    services.mark_material_complete(student_user, course_with_test["lesson1"])
    assert services.lesson_is_unlocked(student_user, course_with_test["lesson2"]) is True
