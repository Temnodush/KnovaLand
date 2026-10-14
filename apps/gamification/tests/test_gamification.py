import pytest

from apps.courses.models import Course, Section
from apps.gamification import services
from apps.gamification.models import (
    Achievement,
    Enrollment,
    MaterialProgress,
    PlayerAchievement,
    PlayerProfile,
)
from apps.materials.models import Material
from apps.testing.models import Choice, Question, Test

pytestmark = pytest.mark.django_db


def test_level_formula():
    assert services.xp_required_for_level(1) == 0
    assert services.xp_required_for_level(2) == 100
    assert services.xp_required_for_level(3) == 300
    assert services.level_for_xp(0) == 1
    assert services.level_for_xp(99) == 1
    assert services.level_for_xp(100) == 2
    assert services.level_for_xp(300) == 3


@pytest.fixture
def course(teacher_user):
    course = Course.objects.create(title="Python", owner=teacher_user)
    section = Section.objects.create(course=course, title="Basics")
    Material.objects.create(section=section, title="M1", owner=teacher_user)
    Material.objects.create(section=section, title="M2", owner=teacher_user)
    return course


def test_award_xp_updates_profile(student_user):
    profile = services.get_profile(student_user)
    services.award_xp(profile, 120, reason="test")
    profile.refresh_from_db()
    assert profile.xp == 120
    assert profile.level == 2
    assert profile.streak_days == 1


def test_profile_xp_properties(student_user):
    profile = services.get_profile(student_user)
    services.award_xp(profile, 150, reason="x")
    profile.refresh_from_db()
    assert profile.xp_in_level == 50
    assert profile.xp_to_next_level == 150
    assert profile.level_progress_percent == 25.0


def test_enroll_awards_xp_and_achievement(student_user, course):
    services.seed_achievements()
    enrollment, created = services.enroll(student_user, course)
    assert created is True
    profile = services.get_profile(student_user)
    profile.refresh_from_db()
    assert profile.xp >= 10
    assert PlayerAchievement.objects.filter(
        profile=profile, achievement__code="first_enrollment"
    ).exists()


def test_material_complete_awards_xp_and_completes_course(student_user, course):
    services.seed_achievements()
    services.enroll(student_user, course)
    materials = list(Material.objects.filter(section__course=course))
    for material in materials:
        services.mark_material_complete(student_user, material)
    enrollment = Enrollment.objects.get(user=student_user, course=course)
    assert enrollment.completed_at is not None
    assert services.course_progress_percent(student_user, course) == 100.0


def test_leaderboard_order(student_user, teacher_user):
    services.award_xp(services.get_profile(student_user), 50)
    services.award_xp(services.get_profile(teacher_user), 200)
    board = list(services.leaderboard())
    assert board[0].user == teacher_user


def test_api_profile(student_client, student_user):
    services.award_xp(services.get_profile(student_user), 30)
    response = student_client.get("/api/game/profile/")
    assert response.status_code == 200
    assert response.data["xp"] == 30
    assert response.data["level"] == 1


def test_api_leaderboard(student_client, student_user, teacher_user):
    services.award_xp(services.get_profile(teacher_user), 500)
    response = student_client.get("/api/game/leaderboard/")
    assert response.status_code == 200
    assert response.data[0]["username"] == teacher_user.username


def test_api_enroll(student_client, student_user, course):
    response = student_client.post("/api/game/enroll/", {"course": course.id}, format="json")
    assert response.status_code == 201
    assert Enrollment.objects.filter(user=student_user, course=course).exists()


def test_api_complete_material(student_client, student_user, course):
    material = Material.objects.filter(section__course=course).first()
    response = student_client.post(
        "/api/game/progress/", {"material": material.id}, format="json"
    )
    assert response.status_code == 201
    assert MaterialProgress.objects.filter(user=student_user, material=material).exists()


def test_test_submission_awards_xp(student_user, teacher_user, course):
    material = Material.objects.filter(section__course=course).first()
    test = Test.objects.create(material=material, title="T", owner=teacher_user)
    question = Question.objects.create(test=test, text="?", order=1)
    correct = Choice.objects.create(question=question, text="ok", is_correct=True)
    from apps.testing.models import TestSubmission

    TestSubmission.objects.create(
        test=test, user=student_user, score=1, total=1, percentage=100.0, is_passed=True
    )
    profile = services.get_profile(student_user)
    profile.refresh_from_db()
    assert profile.xp >= 20  # 10 базовых + 10 за правильный ответ


def test_achievement_catalog_created():
    services.seed_achievements()
    assert Achievement.objects.filter(code="first_enrollment").exists()
    assert Achievement.objects.count() >= 7
