from django.conf import settings
from django.db import models

from apps.courses.models import Course
from apps.materials.models import Material


class PlayerProfile(models.Model):
    """Игровой профиль пользователя: опыт, уровень, серия занятий."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="player_profile",
        verbose_name="Пользователь",
    )
    xp = models.PositiveIntegerField(default=0, verbose_name="Опыт")
    level = models.PositiveIntegerField(default=1, verbose_name="Уровень")
    streak_days = models.PositiveIntegerField(default=0, verbose_name="Серия дней")
    last_activity_date = models.DateField(null=True, blank=True, verbose_name="Последняя активность")
    character = models.CharField(max_length=50, blank=True, verbose_name="Персонаж")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Игровой профиль"
        verbose_name_plural = "Игровые профили"

    def __str__(self):
        return f"{self.user} — ур. {self.level} ({self.xp} XP)"

    @property
    def xp_in_level(self):
        """Опыт, набранный внутри текущего уровня."""
        from .services import xp_required_for_level

        return self.xp - xp_required_for_level(self.level)

    @property
    def xp_to_next_level(self):
        """Сколько опыта осталось до следующего уровня."""
        from .services import xp_required_for_level

        return max(xp_required_for_level(self.level + 1) - self.xp, 0)

    @property
    def level_progress_percent(self):
        from .services import xp_required_for_level

        current = xp_required_for_level(self.level)
        nxt = xp_required_for_level(self.level + 1)
        span = nxt - current
        if span <= 0:
            return 100
        return round((self.xp - current) / span * 100, 1)


class Achievement(models.Model):
    """Справочник достижений (руна/бейдж)."""

    code = models.SlugField(max_length=64, unique=True, verbose_name="Код")
    title = models.CharField(max_length=120, verbose_name="Название")
    description = models.CharField(max_length=255, blank=True, verbose_name="Описание")
    icon = models.CharField(max_length=16, default="🏅", verbose_name="Иконка (emoji)")
    xp_reward = models.PositiveIntegerField(default=0, verbose_name="Бонусный опыт")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Достижение"
        verbose_name_plural = "Достижения"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class PlayerAchievement(models.Model):
    """Полученное пользователем достижение."""

    profile = models.ForeignKey(
        PlayerProfile,
        on_delete=models.CASCADE,
        related_name="achievements",
        verbose_name="Профиль",
    )
    achievement = models.ForeignKey(
        Achievement, on_delete=models.CASCADE, verbose_name="Достижение"
    )
    earned_at = models.DateTimeField(auto_now_add=True, verbose_name="Получено")

    class Meta:
        verbose_name = "Достижение игрока"
        verbose_name_plural = "Достижения игроков"
        unique_together = ("profile", "achievement")
        ordering = ["-earned_at"]

    def __str__(self):
        return f"{self.profile.user} — {self.achievement.title}"


class Enrollment(models.Model):
    """Запись студента на курс (зачисление)."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name="enrollments")
    started_at = models.DateTimeField(auto_now_add=True, verbose_name="Начат")
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name="Завершён")

    class Meta:
        verbose_name = "Зачисление на курс"
        verbose_name_plural = "Зачисления на курсы"
        unique_together = ("user", "course")
        ordering = ["-started_at"]

    def __str__(self):
        return f"{self.user} → {self.course}"

    @property
    def is_completed(self):
        return self.completed_at is not None


class MaterialProgress(models.Model):
    """Отметка о прохождении материала студентом."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="material_progress"
    )
    material = models.ForeignKey(
        Material, on_delete=models.CASCADE, related_name="progress_records"
    )
    completed_at = models.DateTimeField(auto_now_add=True, verbose_name="Завершён")

    class Meta:
        verbose_name = "Прогресс по материалу"
        verbose_name_plural = "Прогресс по материалам"
        unique_together = ("user", "material")
        ordering = ["-completed_at"]

    def __str__(self):
        return f"{self.user} ✓ {self.material}"


class XPTransaction(models.Model):
    """Журнал начисления опыта (для прозрачности и отладки)."""

    profile = models.ForeignKey(
        PlayerProfile, on_delete=models.CASCADE, related_name="transactions"
    )
    amount = models.IntegerField(verbose_name="Опыт")
    reason = models.CharField(max_length=120, blank=True, verbose_name="Причина")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Начисление опыта"
        verbose_name_plural = "Начисления опыта"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.profile.user}: +{self.amount} ({self.reason})"
