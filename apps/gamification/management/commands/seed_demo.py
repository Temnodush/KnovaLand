"""Демонстрационные данные: курс Python с уроками, навыками и тренажёрами.

Запуск: python manage.py seed_demo
"""

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.courses.models import Course, Section
from apps.gamification import services
from apps.gamification.models import SectionSkill, Skill
from apps.materials.models import Material
from apps.testing.models import Choice, Question, Test

User = get_user_model()

# Навыки курса (выдаются за прохождение группы уроков).
SKILLS = [
    ("py-basics", "Базовые знания Python", "Переменные, типы данных и вывод", "🐣", 1),
    ("py-control", "Управление логикой", "Условия, циклы и ветвления", "🔀", 2),
    ("py-collections", "Структуры данных и функции", "Списки и функции", "🧩", 3),
]

COURSE_TITLE = "Python"
COURSE_DESC = (
    "Пошаговый курс по основам Python: от первой программы до собственных функций. "
    "Уроки открываются по мере прохождения, а в конце каждого — тренажёр."
)

# Структура курса: группы уроков (разделы) → уроки → тренажёр.
COURSE_STRUCTURE = [
    {
        "title": "Основы Python",
        "order": 1,
        "skill": "py-basics",
        "lessons": [
            {
                "title": "Знакомство с Python",
                "content": (
                    "## Что такое Python?\n\n"
                    "**Python** — это популярный язык программирования. Его читают почти как "
                    "обычный английский, поэтому он отлично подходит для первого языка.\n\n"
                    "### Первая программа\n\n"
                    "Чтобы вывести текст на экран, используют функцию `print()`:\n\n"
                    "```python\n"
                    'print("Привет, мир!")\n'
                    "```\n\n"
                    "При запуске вы увидите:\n\n"
                    "```\n"
                    "Привет, мир!\n"
                    "```\n\n"
                    "### Комментарии\n\n"
                    "Комментарии начинаются с `#` и не выполняются:\n\n"
                    "```python\n"
                    "# Это комментарий, он только для людей\n"
                    'print("А это выполнится")\n'
                    "```\n\n"
                    "> Совет: строки в Python берутся в кавычки — одинарные `'...'` "
                    'или двойные `"..."`.\n'
                ),
                "questions": [
                    {
                        "text": "Какая функция выводит текст на экран?",
                        "choices": [("print()", True), ("echo()", False), ("console.log()", False)],
                    },
                    {
                        "text": "Как в Python оформляют комментарий?",
                        "choices": [
                            ("Символом #", True),
                            ("// как в C", False),
                            ("Символом --", False),
                        ],
                    },
                ],
            },
            {
                "title": "Переменные и типы данных",
                "content": (
                    "## Переменные\n\n"
                    "**Переменная** — это имя, под которым хранится значение. В Python не нужно "
                    "заранее указывать тип:\n\n"
                    "```python\n"
                    'name = "Ада"\n'
                    "age = 36\n"
                    "height = 1.7\n"
                    "is_student = True\n"
                    "```\n\n"
                    "### Основные типы\n\n"
                    "| Тип | Пример | Назначение |\n"
                    "| --- | --- | --- |\n"
                    '| `str` | `"текст"` | строка |\n'
                    "| `int` | `42` | целое число |\n"
                    "| `float` | `3.14` | дробное число |\n"
                    "| `bool` | `True` / `False` | логический |\n\n"
                    "Проверить тип можно функцией `type()`:\n\n"
                    "```python\n"
                    "print(type(42))\n"
                    "```\n"
                ),
                "questions": [
                    {
                        "text": "Какой тип у значения 3.14?",
                        "choices": [("float", True), ("int", False), ("str", False)],
                    },
                    {
                        "text": "Как хранить логическое значение?",
                        "choices": [("Типом bool (True/False)", True), ("Строкой 'yes'", False)],
                    },
                ],
            },
            {
                "title": "Числа и ввод данных",
                "content": (
                    "## Арифметика\n\n"
                    "Python умеет считать как калькулятор:\n\n"
                    "```python\n"
                    "print(2 + 3)    # 5\n"
                    "print(10 / 4)   # 2.5\n"
                    "print(10 // 4)  # 2  целочисленное деление\n"
                    "print(10 % 3)   # 1  остаток\n"
                    "print(2 ** 3)   # 8  возведение в степень\n"
                    "```\n\n"
                    "## Ввод данных\n\n"
                    "Функция `input()` читает строку, введённую пользователем:\n\n"
                    "```python\n"
                    'name = input("Как вас зовут? ")\n'
                    'print("Привет, " + name)\n'
                    "```\n\n"
                    "> Важно: `input()` всегда возвращает **строку**. Чтобы получить число, "
                    "используйте `int()`:\n\n"
                    "```python\n"
                    'age = int(input("Возраст: "))\n'
                    "print(age + 1)\n"
                    "```\n"
                ),
                "questions": [
                    {
                        "text": "Что вернёт 10 // 4 ?",
                        "choices": [("2", True), ("2.5", False), ("2.0", False)],
                    },
                    {
                        "text": "Что возвращает input()?",
                        "choices": [("Строку", True), ("Число", False), ("Список", False)],
                    },
                ],
            },
        ],
    },
    {
        "title": "Условия и циклы",
        "order": 2,
        "skill": "py-control",
        "lessons": [
            {
                "title": "Условный оператор if",
                "content": (
                    "## Ветвление\n\n"
                    "`if` выполняет код, только если условие истинно:\n\n"
                    "```python\n"
                    "age = 18\n"
                    "if age >= 18:\n"
                    '    print("Взрослый")\n'
                    "else:\n"
                    '    print("Ребёнок")\n'
                    "```\n\n"
                    "### Отступы\n\n"
                    "В Python блок кода выделяют **отступом** (обычно 4 пробела). "
                    "Отступы — часть синтаксиса!\n\n"
                    "### elif\n\n"
                    "Можно проверять несколько условий по порядку:\n\n"
                    "```python\n"
                    "score = 75\n"
                    "if score >= 90:\n"
                    '    print("5")\n'
                    "elif score >= 70:\n"
                    '    print("4")\n'
                    "else:\n"
                    '    print("3")\n'
                    "```\n\n"
                    "### Операторы сравнения\n\n"
                    "`==` равно, `!=` не равно, `>` `<` `>=` `<=`, а `and` / `or` / `not` "
                    "объединяют условия.\n"
                ),
                "questions": [
                    {
                        "text": "Чем выделяется блок кода в Python?",
                        "choices": [
                            ("Отступом", True),
                            ("Фигурными скобками {}", False),
                            ("Словом begin", False),
                        ],
                    },
                    {
                        "text": "Какое слово проверяет дополнительное условие?",
                        "choices": [("elif", True), ("elseif", False), ("elsif", False)],
                    },
                    {
                        "text": "Как обозначается проверка на равенство?",
                        "choices": [("==", True), ("=", False), ("===", False)],
                    },
                ],
            },
            {
                "title": "Циклы for и while",
                "content": (
                    "## Цикл for\n\n"
                    "Проходит по элементам последовательности:\n\n"
                    "```python\n"
                    "for i in range(5):\n"
                    "    print(i)   # 0 1 2 3 4\n"
                    "```\n\n"
                    "`range(5)` даёт числа от 0 до 4. Можно перебрать строку:\n\n"
                    "```python\n"
                    "for letter in 'кот':\n"
                    "    print(letter)\n"
                    "```\n\n"
                    "## Цикл while\n\n"
                    "Повторяет, пока условие истинно:\n\n"
                    "```python\n"
                    "n = 3\n"
                    "while n > 0:\n"
                    "    print(n)\n"
                    "    n = n - 1\n"
                    "# 3 2 1\n"
                    "```\n\n"
                    "> Осторожно: если условие никогда не станет ложным — цикл зациклится.\n\n"
                    "Команды `break` (выйти) и `continue` (перейти к следующей итерации) "
                    "управляют циклом.\n"
                ),
                "questions": [
                    {
                        "text": "Что напечатает range(3)?",
                        "choices": [("0 1 2", True), ("1 2 3", False), ("0 1 2 3", False)],
                    },
                    {
                        "text": "Какая команда прерывает цикл досрочно?",
                        "choices": [("break", True), ("stop", False), ("exit", False)],
                    },
                ],
            },
            {
                "title": "Списки (list)",
                "content": (
                    "## Списки\n\n"
                    "**Список** хранит несколько значений по порядку:\n\n"
                    "```python\n"
                    "fruits = ['яблоко', 'банан', 'вишня']\n"
                    "print(fruits[0])    # яблоко\n"
                    "print(len(fruits))  # 3\n"
                    "```\n\n"
                    "Индексация начинается с **0**. Обращение `fruits[-1]` берёт "
                    "последний элемент.\n\n"
                    "### Изменение\n\n"
                    "```python\n"
                    "fruits.append('груша')   # добавить в конец\n"
                    "fruits[0] = 'слива'      # заменить элемент\n"
                    "```\n\n"
                    "### Срез\n\n"
                    "```python\n"
                    "print(fruits[1:3])  # элементы с индекса 1 по 2\n"
                    "```\n\n"
                    "Перебрать список удобно циклом `for`:\n\n"
                    "```python\n"
                    "for fruit in fruits:\n"
                    "    print(fruit)\n"
                    "```\n"
                ),
                "questions": [
                    {
                        "text": "С какого индекса начинается нумерация в списке?",
                        "choices": [("С 0", True), ("С 1", False), ("С -1", False)],
                    },
                    {
                        "text": "Как добавить элемент в конец списка?",
                        "choices": [(".append()", True), (".push()", False), (".add()", False)],
                    },
                ],
            },
        ],
    },
    {
        "title": "Функции",
        "order": 3,
        "skill": "py-collections",
        "lessons": [
            {
                "title": "Функции",
                "content": (
                    "## Зачем функции\n\n"
                    "Функция — это именованный блок кода, который можно вызывать много раз.\n\n"
                    "```python\n"
                    "def greet(name):\n"
                    '    return "Привет, " + name\n\n'
                    'print(greet("Ада"))  # Привет, Ада\n'
                    "```\n\n"
                    "### Разбор\n\n"
                    "- `def` — объявление функции;\n"
                    "- `greet` — имя;\n"
                    "- `name` — параметр;\n"
                    "- `return` — возвращает результат.\n\n"
                    "### Значение по умолчанию\n\n"
                    "```python\n"
                    "def power(x, exponent=2):\n"
                    "    return x ** exponent\n\n"
                    "print(power(3))     # 9\n"
                    "print(power(2, 3))  # 8\n"
                    "```\n\n"
                    "> Функции помогают не повторять один и тот же код и делают "
                    "программу понятнее.\n"
                ),
                "questions": [
                    {
                        "text": "Каким словом объявляют функцию?",
                        "choices": [("def", True), ("func", False), ("function", False)],
                    },
                    {
                        "text": "Что возвращает значение из функции?",
                        "choices": [("return", True), ("print", False), ("yield-only", False)],
                    },
                    {
                        "text": "Что делает power(3) из примера?",
                        "choices": [
                            ("Возвращает 3 в квадрате = 9", True),
                            ("Возвращает 3", False),
                        ],
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные для показа платформы (курс Python)."

    @transaction.atomic
    def handle(self, *args, **options):
        services.seed_achievements()
        skills = self._seed_skills()
        self.stdout.write(self.style.SUCCESS("Достижения и навыки созданы."))

        self._user("admin", "admin@example.com", "admin12345", User.Role.ADMIN, True, True)
        teacher = self._user("teacher", "teacher@example.com", "teacher12345", User.Role.TEACHER)
        self._user("student", "student@example.com", "student12345", User.Role.STUDENT)

        # Чистим прежние курсы, чтобы структура обновилась.
        Course.objects.filter(
            title__in=[COURSE_TITLE, "Основы Python", "Управление версиями с Git"]
        ).delete()

        course = Course.objects.create(
            title=COURSE_TITLE, description=COURSE_DESC, owner=teacher, is_published=True
        )
        for section_data in COURSE_STRUCTURE:
            self._create_section(course, teacher, section_data, skills)

        self.stdout.write(
            self.style.SUCCESS(
                "Готово: курс «Python» с 7 уроками и 3 навыками.\n"
                "  admin   / admin12345\n"
                "  teacher / teacher12345\n"
                "  student / student12345"
            )
        )

    def _seed_skills(self):
        result = {}
        for code, title, desc, icon, order in SKILLS:
            skill, _ = Skill.objects.update_or_create(
                code=code,
                defaults={"title": title, "description": desc, "icon": icon, "order": order},
            )
            result[code] = skill
        return result

    def _create_section(self, course, teacher, data, skills):
        section = Section.objects.create(course=course, title=data["title"], order=data["order"])
        skill = skills.get(data.get("skill"))
        if skill:
            SectionSkill.objects.create(section=section, skill=skill)

        for order, lesson_data in enumerate(data["lessons"], start=1):
            material = Material.objects.create(
                section=section,
                title=lesson_data["title"],
                content=lesson_data["content"],
                order=order,
                owner=teacher,
            )
            self._create_test(material, teacher, lesson_data["questions"])

    def _create_test(self, material, teacher, questions):
        test = Test.objects.create(
            material=material,
            title=f"Тренажёр: {material.title}",
            owner=teacher,
            passing_score=60,
        )
        for order, q in enumerate(questions, start=1):
            question = Question.objects.create(test=test, text=q["text"], order=order)
            for choice_text, is_correct in q["choices"]:
                Choice.objects.create(question=question, text=choice_text, is_correct=is_correct)

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
