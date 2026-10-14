import pytest
from django.core.management import call_command

from apps.courses.models import Course
from apps.gamification.models import SectionSkill, Skill
from apps.materials.models import Material
from apps.testing.models import Test

pytestmark = pytest.mark.django_db


def test_seed_demo_creates_all_courses():
    call_command("seed_demo")

    titles = set(Course.objects.values_list("title", flat=True))
    assert {"Python", "JavaScript", "C#", "Java"} <= titles

    assert Course.objects.count() == 4
    assert Material.objects.count() == 28
    assert Test.objects.count() == 28
    assert Skill.objects.count() == 12

    for course in Course.objects.all():
        assert Material.objects.filter(section__course=course).count() == 7
        assert SectionSkill.objects.filter(section__course=course).count() == 3


def test_seed_demo_is_idempotent():
    call_command("seed_demo")
    call_command("seed_demo")
    # Повторный запуск не плодит дубли курсов.
    assert Course.objects.count() == 4
    assert Material.objects.count() == 28


def test_seed_demo_text_questions_present():
    call_command("seed_demo")
    from apps.testing.models import Question

    assert Question.objects.filter(kind=Question.Kind.TEXT).exists()
