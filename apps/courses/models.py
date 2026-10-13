from django.conf import settings
from django.db import models


class Course(models.Model):
    """Курс — верхнеуровневая сущность, принадлежит преподавателю (владельцу)."""

    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="courses",
        verbose_name="Владелец",
    )
    is_published = models.BooleanField(default=True, verbose_name="Опубликован")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Курс"
        verbose_name_plural = "Курсы"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Section(models.Model):
    """Раздел внутри курса."""

    course = models.ForeignKey(
        Course,
        on_delete=models.CASCADE,
        related_name="sections",
        verbose_name="Курс",
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Раздел"
        verbose_name_plural = "Разделы"
        ordering = ["order", "id"]

    def __str__(self):
        return f"{self.course.title} / {self.title}"

    @property
    def owner(self):
        """Владелец раздела — владелец его курса (для проверки прав)."""
        return self.course.owner
