import re

from django.conf import settings
from django.db import models

from apps.materials.models import Material


def normalize_answer(value):
    """Привести текстовый ответ к сравнимому виду: регистр, пробелы, край пробелов."""
    return re.sub(r"\s+", " ", (value or "").strip().lower())


class Test(models.Model):
    """Тест, привязанный к материалу.

    Один материал может содержать несколько тестов.
    """

    # Не даём pytest воспринимать модель как тест-класс.
    __test__ = False

    material = models.ForeignKey(
        Material,
        on_delete=models.CASCADE,
        related_name="tests",
        verbose_name="Материал",
    )
    title = models.CharField(max_length=255, verbose_name="Название")
    description = models.TextField(blank=True, verbose_name="Описание")
    passing_score = models.PositiveSmallIntegerField(default=60, verbose_name="Проходной балл (%)")
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="tests",
        verbose_name="Владелец",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Тест"
        verbose_name_plural = "Тесты"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def questions_count(self):
        return self.questions.count()


class Question(models.Model):
    class Kind(models.TextChoices):
        CHOICE = "choice", "Выбор ответа"
        TEXT = "text", "Ручной ввод"

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="questions",
        verbose_name="Тест",
    )
    text = models.TextField(verbose_name="Вопрос")
    kind = models.CharField(
        max_length=10,
        choices=Kind.choices,
        default=Kind.CHOICE,
        verbose_name="Тип вопроса",
    )
    answer_text = models.CharField(
        max_length=500,
        blank=True,
        verbose_name="Правильный ответ (для ручного ввода)",
        help_text="Несколько допустимых вариантов разделяйте символом |",
    )
    order = models.PositiveIntegerField(default=0, verbose_name="Порядок")

    class Meta:
        verbose_name = "Вопрос"
        verbose_name_plural = "Вопросы"
        ordering = ["order", "id"]

    def __str__(self):
        return self.text[:60]

    def correct_choice_ids(self):
        return list(self.choices.filter(is_correct=True).values_list("id", flat=True))

    def correct_text_answers(self):
        """Список допустимых ответов (нормализованных) для вопроса с вводом."""
        return [normalize_answer(part) for part in self.answer_text.split("|") if part.strip()]

    def check_text(self, value):
        return normalize_answer(value) in self.correct_text_answers()


class Choice(models.Model):
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="choices",
        verbose_name="Вопрос",
    )
    text = models.CharField(max_length=500, verbose_name="Вариант ответа")
    is_correct = models.BooleanField(default=False, verbose_name="Правильный")

    class Meta:
        verbose_name = "Вариант ответа"
        verbose_name_plural = "Варианты ответа"
        ordering = ["id"]

    def __str__(self):
        return self.text[:60]


class TestSubmission(models.Model):
    """Результат прохождения теста студентом."""

    test = models.ForeignKey(
        Test,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Тест",
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="submissions",
        verbose_name="Студент",
    )
    score = models.PositiveIntegerField(default=0, verbose_name="Баллы")
    total = models.PositiveIntegerField(default=0, verbose_name="Всего вопросов")
    percentage = models.FloatField(default=0.0, verbose_name="Процент")
    is_passed = models.BooleanField(default=False, verbose_name="Пройден")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Результат теста"
        verbose_name_plural = "Результаты тестов"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} — {self.test} ({self.score}/{self.total})"


class SubmissionAnswer(models.Model):
    submission = models.ForeignKey(
        TestSubmission,
        on_delete=models.CASCADE,
        related_name="answers",
        verbose_name="Результат",
    )
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name="Вопрос")
    selected_choices = models.ManyToManyField(Choice, verbose_name="Выбранные ответы")
    text_answer = models.CharField(
        max_length=500, blank=True, verbose_name="Введённый ответ (ручной ввод)"
    )
    is_correct = models.BooleanField(default=False, verbose_name="Ответ верный")

    class Meta:
        verbose_name = "Ответ на вопрос"
        verbose_name_plural = "Ответы на вопросы"

    def __str__(self):
        return f"Q{self.question_id}: {'верно' if self.is_correct else 'неверно'}"
