import pytest

from apps.courses.models import Course, Section
from apps.gamification import services
from apps.gamification.models import Enrollment, PlayerSkill, SectionSkill, Skill
from apps.materials.models import Material

pytestmark = pytest.mark.django_db


@pytest.fixture
def lesson_setup(teacher_user):
    course = Course.objects.create(title="Py", owner=teacher_user, is_published=True)
    section = Section.objects.create(course=course, title="S1", order=1)
    skill = Skill.objects.create(code="basics", title="Базовые знания")
    SectionSkill.objects.create(section=section, skill=skill)
    lessons = [
        Material.objects.create(section=section, title=f"L{i}", owner=teacher_user, order=i)
        for i in range(1, 4)
    ]
    return {"course": course, "section": section, "skill": skill, "lessons": lessons}


def test_first_lesson_unlocked_only(student_user, lesson_setup):
    first, second, _ = lesson_setup["lessons"]
    assert services.lesson_is_unlocked(student_user, first) is True
    assert services.lesson_is_unlocked(student_user, second) is False


def test_next_lesson_unlocks_after_completion(student_user, lesson_setup):
    first, second, _ = lesson_setup["lessons"]
    services.mark_material_complete(student_user, first)
    assert services.lesson_is_unlocked(student_user, second) is True


def test_skill_granted_after_group_complete(student_user, lesson_setup):
    profile = services.get_profile(student_user)
    assert not PlayerSkill.objects.filter(profile=profile).exists()
    for lesson in lesson_setup["lessons"]:
        services.mark_material_complete(student_user, lesson)
    assert PlayerSkill.objects.filter(profile=profile, skill=lesson_setup["skill"]).exists()


def test_course_level_grows_with_lessons(student_user, lesson_setup):
    course = lesson_setup["course"]
    services.enroll(student_user, course)
    services.mark_material_complete(student_user, lesson_setup["lessons"][0])
    enrollment = Enrollment.objects.get(user=student_user, course=course)
    assert enrollment.xp >= services.XP_PER_LESSON
    assert enrollment.course_level >= 2
    assert 0 <= enrollment.course_level_progress_percent <= 100


def test_next_lesson_helper(student_user, lesson_setup):
    course = lesson_setup["course"]
    assert services.next_lesson(student_user, course) == lesson_setup["lessons"][0]
    services.mark_material_complete(student_user, lesson_setup["lessons"][0])
    assert services.next_lesson(student_user, course) == lesson_setup["lessons"][1]


def test_course_level_formula():
    assert services.course_level_for_xp(0) == 1
    assert services.course_level_for_xp(99) == 1
    assert services.course_level_for_xp(100) == 2
    assert services.course_level_for_xp(250) == 3
