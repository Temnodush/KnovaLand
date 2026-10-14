import pytest
from django.test import Client
from django.urls import reverse

from apps.courses.models import Course
from apps.gamification import services
from apps.gamification.models import Enrollment, Purchase
from apps.gamification.services import XP_PER_PURCHASE

pytestmark = pytest.mark.django_db


@pytest.fixture
def free_course(teacher_user):
    return Course.objects.create(title="Free", owner=teacher_user, price=0, is_published=True)


@pytest.fixture
def paid_course(teacher_user):
    return Course.objects.create(title="Paid", owner=teacher_user, price=990, is_published=True)


def test_user_has_access_free(free_course, student_user):
    assert services.user_has_access(student_user, free_course) is True


def test_user_has_no_access_to_paid_without_purchase(paid_course, student_user):
    assert services.user_has_access(student_user, paid_course) is False


def test_purchase_course_grants_access_and_enrollment(paid_course, student_user):
    profile = services.get_profile(student_user)
    purchase, created = services.purchase_course(student_user, paid_course)
    assert created is True
    assert purchase.amount == paid_course.price
    assert services.user_has_access(student_user, paid_course) is True
    assert Enrollment.objects.filter(user=student_user, course=paid_course).exists()
    profile.refresh_from_db()
    assert profile.xp >= XP_PER_PURCHASE


def test_purchase_is_idempotent(paid_course, student_user):
    services.purchase_course(student_user, paid_course)
    _, created = services.purchase_course(student_user, paid_course)
    assert created is False
    assert Purchase.objects.filter(user=student_user, course=paid_course).count() == 1


def test_api_enroll_paid_course_requires_purchase(student_client, paid_course):
    response = student_client.post("/api/game/enroll/", {"course": paid_course.id}, format="json")
    assert response.status_code == 402


def test_api_purchase_then_enroll(student_client, paid_course, student_user):
    response = student_client.post("/api/game/purchase/", {"course": paid_course.id}, format="json")
    assert response.status_code == 201
    assert response.data["purchased"] is True
    enroll = student_client.post("/api/game/enroll/", {"course": paid_course.id}, format="json")
    assert enroll.status_code in (200, 201)


def test_api_purchase_free_course_rejected(student_client, free_course):
    response = student_client.post("/api/game/purchase/", {"course": free_course.id}, format="json")
    assert response.status_code == 400


def test_api_enroll_free_course_ok(student_client, free_course):
    response = student_client.post("/api/game/enroll/", {"course": free_course.id}, format="json")
    assert response.status_code == 201


def test_web_buy_course(paid_course, student_user):
    client = Client()
    client.force_login(student_user)
    response = client.post(reverse("web:buy", kwargs={"pk": paid_course.id}))
    assert response.status_code == 302
    assert Purchase.objects.filter(user=student_user, course=paid_course).exists()


def test_web_enroll_paid_without_purchase_redirects(paid_course, student_user):
    client = Client()
    client.force_login(student_user)
    response = client.post(reverse("web:enroll", kwargs={"pk": paid_course.id}))
    assert response.status_code == 302
    assert not Enrollment.objects.filter(user=student_user, course=paid_course).exists()
