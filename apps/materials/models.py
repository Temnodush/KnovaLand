from django.conf import settings
from django.db import models

from apps.courses.models import Section


class Material(models.Model):
    """Учебный материал внутри раздела."""

    section = models.ForeignKey(
        Section,
        on_delete=models.CASCADE,
        related_name="materials",
        verbose_name="Раздел",
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    content = models.TextField(blank=True, verbose_name="Содержание")
    video_url = models.URLField(blank=True, verbose_name="Ссылка на видео")
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="materials",
        verbose_name="Владелец",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Материал"
        verbose_name_plural = "Материалы"
        ordering = ["order", "id"]

    def __str__(self):
        return self.title
