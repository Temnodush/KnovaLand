"""Демонстрационные данные: пользователи, курсы, материалы, тесты, достижения.

Запуск: python manage.py seed_demo
"""
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.courses.models import Course, Section
from apps.gamification import services
from apps.materials.models import Material
from apps.testing.models import Choice, Question, Test

User = get_user_model()


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные для показа платформы."

    @transaction.atomic
    def handle(self, *args, **options):
        services.seed_achievements()
        self.stdout.write(self.style.SUCCESS("Достижения созданы."))

        admin = self._user("admin", "admin@example.com", "admin12345", User.Role.ADMIN, True, True)
        teacher = self._user("teacher", "teacher@example.com", "teacher12345", User.Role.TEACHER)
        student = self._user("student", "student@example.com", "student12345", User.Role.STUDENT)

        self._course(
            teacher,
            "Основы Python",
            "Переменные, типы, условия и циклы в Python.",
            [
                (
                    "Знакомство",
                    [
                        ("Что такое Python", "Python — язык программирования общего назначения."),
                        ("Первая программа", 'print("Hello, world!") — ваша первая строка.'),
                    ],
                ),
                (
                    "Переменные и типы",
                    [("Переменные", "x = 10, name = 'Ада' — присваивание значений.")],
                ),
            ],
            self._python_test,
        )

        self._course(
            teacher,
            "Управление версиями с Git",
            "Базовые операции Git: репозиторий, коммиты, ветки.",
            [
                (
                    "Основы",
                    [
                        ("Репозиторий", "git init создаёт новый репозиторий."),
                        ("Первый коммит", "git add . && git commit -m 'init'."),
                    ],
                ),
            ],
            None,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Демо-данные готовы.\n"
                "  admin   / admin12345   (администратор)\n"
                "  teacher / teacher12345 (преподаватель)\n"
                "  student / student12345 (студент)"
            )
        )

    def _user(self, username, email, password, role, is_staff=False, is_superuser=False):
        user, created = User.objects.get_or_create(
            username=username,
            defaults={
                "email": email,
                "role": role,
                "is_staff": is_staff,
                "is_superuser": is_superuser,
            },
        )
        if created:
            user.set_password(password)
            user.save()
            self.stdout.write(f"  + пользователь {username}")
        return user

    def _course(self, teacher, title, description, sections, test_builder):
        course, _ = Course.objects.get_or_create(
            title=title, owner=teacher, defaults={"description": description}
        )
        for order, (section_title, materials) in enumerate(sections, start=1):
            section, _ = Section.objects.get_or_create(
                course=course, title=section_title, defaults={"order": order}
            )
            for m_order, (m_title, m_content) in enumerate(materials, start=1):
                material, _ = Material.objects.get_or_create(
                    section=section,
                    title=m_title,
                    defaults={"content": m_content, "order": m_order, "owner": teacher},
                )
                if test_builder and not material.tests.exists():
                    test_builder(material, teacher)
        return course

    def _python_test(self, material, teacher):
        test = Test.objects.create(
            material=material,
            title=f"Проверка: {material.title}",
            owner=teacher,
            passing_score=60,
        )
        q1 = Question.objects.create(test=test, text="Какая функция выводит текст на экран?", order=1)
        Choice.objects.create(question=q1, text="print()", is_correct=True)
        Choice.objects.create(question=q1, text="echo()", is_correct=False)
        Choice.objects.create(question=q1, text="console.log()", is_correct=False)
