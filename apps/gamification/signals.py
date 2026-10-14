"""Сигналы: автоматическое начисление опыта и проверка достижений."""

from django.db.models.signals import post_save
from django.dispatch import receiver

from apps.testing.models import TestSubmission

from . import services
from .models import Enrollment, MaterialProgress


@receiver(post_save, sender=TestSubmission)
def on_test_submission(sender, instance, created, **kwargs):
    """Начислить глобальный и курсовой опыт за сданный тест.

    Глобально: 10 + 10 за каждый правильный ответ.
    Курсовой опыт — только при успешной сдаче (passing_score).
    """
    if not created:
        return
    profile = services.get_profile(instance.user)
    reward = 10 + instance.score * 10
    services.award_xp(profile, reward, reason=f"test:{instance.test_id}")
    if instance.is_passed:
        course = instance.test.material.section.course
        services.award_course_xp(
            instance.user,
            course,
            services.XP_PER_TRAINER_PASS,
            reason=f"trainer:{instance.test_id}",
        )


@receiver(post_save, sender=MaterialProgress)
def on_material_progress(sender, instance, created, **kwargs):
    """Проверить завершение курса при отметке материала."""
    if created:
        course = instance.material.section.course
        services.refresh_course_completion(instance.user, course)


@receiver(post_save, sender=Enrollment)
def on_enrollment(sender, instance, created, **kwargs):
    """Проверить достижения при зачислении."""
    if created:
        services.check_achievements(services.get_profile(instance.user))
