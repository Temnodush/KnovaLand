"""Демонстрационные данные: 4 курса (Python, JavaScript, C#, Java) с уроками и навыками.

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

# Все навыки (выдаются за прохождение группы уроков).
SKILLS = [
    # Python
    ("py-basics", "Базовые знания Python", "Переменные, типы данных и вывод", "🐣", 1),
    ("py-control", "Управление логикой Python", "Условия, циклы и ветвления", "🔀", 2),
    ("py-collections", "Структуры данных и функции Python", "Списки и функции", "🧩", 3),
    # JavaScript
    ("js-basics", "Основы JavaScript", "Переменные, типы и вывод", "🟨", 10),
    ("js-functions", "Функции и структуры JS", "Функции, массивы и объекты", "🧱", 11),
    ("js-dom", "Работа с DOM", "Поиск элементов и события", "🖱️", 12),
    # C#
    ("cs-basics", "Основы C#", "Переменные, типы и вывод", "🟪", 20),
    ("cs-collections", "Циклы и коллекции C#", "Циклы, массивы и List", "📚", 21),
    ("cs-oop", "ООП в C#", "Классы и объекты", "🏛️", 22),
    # Java
    ("java-basics", "Основы Java", "Вывод, переменные и типы", "☕", 30),
    ("java-collections", "Циклы и массивы Java", "Циклы, массивы и методы", "📦", 31),
    ("java-oop", "ООП в Java", "Классы и объекты", "🏗️", 32),
]

LEGACY_TITLES = [
    "Python",
    "JavaScript",
    "C#",
    "Java",
    "Основы Python",
    "Управление версиями с Git",
]

COURSES = [
    # ------------------------------------------------------------------ Python
    {
        "title": "Python",
        "icon": "🐍",
        "cover": "card_python.png",
        "description": (
            "Пошаговый курс по основам Python: от первой программы до собственных функций. "
            "Уроки открываются по мере прохождения, а в конце каждого — тренажёр."
        ),
        "sections": [
            {
                "title": "Основы Python",
                "order": 1,
                "skill": "py-basics",
                "lessons": [
                    {
                        "title": "Знакомство с Python",
                        "content": (
                            "## Что такое Python?\n\n"
                            "**Python** — популярный язык программирования. Его читают почти "
                            "как обычный английский, поэтому он отлично подходит для старта.\n\n"
                            "### Первая программа\n\n"
                            "Чтобы вывести текст на экран, используют функцию `print()`:\n\n"
                            "```python\n"
                            'print("Привет, мир!")\n'
                            "```\n\n"
                            "### Комментарии\n\n"
                            "Комментарии начинаются с `#` и не выполняются:\n\n"
                            "```python\n"
                            "# Это комментарий\n"
                            'print("А это выполнится")\n'
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Какая функция выводит текст на экран? (выберите)",
                                "choices": [
                                    ("print()", True),
                                    ("echo()", False),
                                    ("console.log()", False),
                                ],
                            },
                            {
                                "text": "Напишите имя функции вывода без скобок",
                                "kind": "text",
                                "answer_text": "print",
                            },
                        ],
                    },
                    {
                        "title": "Переменные и типы данных",
                        "content": (
                            "## Переменные\n\n"
                            "**Переменная** — имя, под которым хранится значение. Тип указывать "
                            "не нужно:\n\n"
                            "```python\n"
                            'name = "Ада"\n'
                            "age = 36\n"
                            "height = 1.7\n"
                            "is_student = True\n"
                            "```\n\n"
                            "### Основные типы\n\n"
                            "| Тип | Пример |\n| --- | --- |\n"
                            '| `str` | `"текст"` |\n| `int` | `42` |\n'
                            "| `float` | `3.14` |\n| `bool` | `True` / `False` |\n"
                        ),
                        "questions": [
                            {
                                "text": "Какой тип у значения 3.14? (выберите)",
                                "choices": [("float", True), ("int", False), ("str", False)],
                            },
                            {
                                "text": "Напишите название типа дробного числа (ручной ввод)",
                                "kind": "text",
                                "answer_text": "float",
                            },
                        ],
                    },
                    {
                        "title": "Числа и ввод данных",
                        "content": (
                            "## Арифметика\n\n"
                            "```python\n"
                            "print(2 + 3)    # 5\n"
                            "print(10 / 4)   # 2.5\n"
                            "print(10 // 4)  # 2  целочисленное деление\n"
                            "print(10 % 3)   # 1  остаток\n"
                            "print(2 ** 3)   # 8  степень\n"
                            "```\n\n"
                            "## Ввод данных\n\n"
                            "`input()` читает строку. Чтобы получить число, "
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
                            "```python\n"
                            "age = 18\n"
                            "if age >= 18:\n"
                            '    print("Взрослый")\n'
                            "else:\n"
                            '    print("Ребёнок")\n'
                            "```\n\n"
                            "Блок кода выделяют **отступом**. Проверку на равенство пишут `==`, "
                            "а `and` / `or` / `not` объединяют условия.\n"
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
                                "text": "Как обозначается проверка на равенство?",
                                "choices": [("==", True), ("=", False), ("===", False)],
                            },
                        ],
                    },
                    {
                        "title": "Циклы for и while",
                        "content": (
                            "## Цикл for\n\n"
                            "```python\n"
                            "for i in range(5):\n"
                            "    print(i)   # 0 1 2 3 4\n"
                            "```\n\n"
                            "## Цикл while\n\n"
                            "```python\n"
                            "n = 3\n"
                            "while n > 0:\n"
                            "    print(n)\n"
                            "    n = n - 1\n"
                            "```\n\n"
                            "`break` выходит из цикла, `continue` переходит к следующей итерации.\n"
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
                            "```python\n"
                            "fruits = ['яблоко', 'банан', 'вишня']\n"
                            "print(fruits[0])    # яблоко\n"
                            "print(len(fruits))  # 3\n"
                            "```\n\n"
                            "Индексация с **0**. `fruits.append('груша')` добавляет в конец, "
                            "`fruits[1:3]` берёт срез.\n"
                        ),
                        "questions": [
                            {
                                "text": "С какого индекса начинается нумерация в списке?",
                                "choices": [("С 0", True), ("С 1", False), ("С -1", False)],
                            },
                            {
                                "text": "Как добавить элемент в конец списка?",
                                "choices": [
                                    (".append()", True),
                                    (".push()", False),
                                    (".add()", False),
                                ],
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
                            "```python\n"
                            "def greet(name):\n"
                            '    return "Привет, " + name\n\n'
                            'print(greet("Ада"))  # Привет, Ада\n'
                            "```\n\n"
                            "`def` объявляет функцию, `return` возвращает результат. "
                            "Значение по умолчанию: `def power(x, exponent=2)`.\n"
                        ),
                        "questions": [
                            {
                                "text": "Каким словом объявляют функцию?",
                                "choices": [("def", True), ("func", False), ("function", False)],
                            },
                            {
                                "text": "Что возвращает значение из функции?",
                                "choices": [("return", True), ("print", False), ("out", False)],
                            },
                        ],
                    },
                ],
            },
        ],
    },
    # -------------------------------------------------------------- JavaScript
    {
        "title": "JavaScript",
        "icon": "🟨",
        "cover": "javascript.png",
        "description": (
            "Основы языка JavaScript: переменные, функции, массивы и работа с DOM. "
            "Язык, который оживляет веб-страницы в браузере."
        ),
        "sections": [
            {
                "title": "Основы JavaScript",
                "order": 1,
                "skill": "js-basics",
                "lessons": [
                    {
                        "title": "Введение в JavaScript",
                        "content": (
                            "## Что такое JavaScript?\n\n"
                            "**JavaScript (JS)** — язык программирования, который выполняется "
                            "в браузере и делает страницы интерактивными.\n\n"
                            "### Вывод в консоль\n\n"
                            "```javascript\n"
                            'console.log("Привет, мир!");\n'
                            "```\n\n"
                            "Консоль открывается в браузере клавишей `F12` (вкладка Console).\n\n"
                            "### Комментарии\n\n"
                            "```javascript\n"
                            "// однострочный\n"
                            "/* многострочный */\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Какая функция выводит текст в консоль?",
                                "choices": [
                                    ("console.log()", True),
                                    ("print()", False),
                                    ("echo()", False),
                                ],
                            },
                            {
                                "text": "Напишите, с какого слова начинается вывод в консоль",
                                "kind": "text",
                                "answer_text": "console",
                            },
                        ],
                    },
                    {
                        "title": "Переменные и типы",
                        "content": (
                            "## Переменные\n\n"
                            "В современном JS используют `let` (изменяемая) и `const` "
                            "(константа):\n\n"
                            "```javascript\n"
                            'let name = "Ада";\n'
                            "let age = 36;\n"
                            "const PI = 3.14;\n"
                            "```\n\n"
                            "### Типы\n\n"
                            "- `number` — числа: `42`, `3.14`;\n"
                            '- `string` — строки: `"текст"`;\n'
                            "- `boolean` — `true` / `false`;\n"
                            "- `null` и `undefined`.\n\n"
                            "`typeof value` показывает тип.\n"
                        ),
                        "questions": [
                            {
                                "text": "Какое слово объявляет константу?",
                                "choices": [("const", True), ("let", False), ("var", False)],
                            },
                            {
                                "text": 'Что вернёт typeof "текст"?',
                                "choices": [("string", True), ("text", False), ("str", False)],
                            },
                        ],
                    },
                    {
                        "title": "Операторы и условия",
                        "content": (
                            "## Условия\n\n"
                            "```javascript\n"
                            "let age = 18;\n"
                            "if (age >= 18) {\n"
                            '  console.log("Взрослый");\n'
                            "} else {\n"
                            '  console.log("Ребёнок");\n'
                            "}\n"
                            "```\n\n"
                            "Строгое сравнение — `===`, нестрогое — `==`. Лучше всегда `===`.\n\n"
                            "```javascript\n"
                            'console.log(2 === "2");  // false\n'
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Какой оператор — строгое сравнение?",
                                "choices": [("===", True), ("==", False), ("=>", False)],
                            },
                            {
                                "text": "Чем выделяют блок кода в JavaScript?",
                                "choices": [
                                    ("Фигурными скобками {}", True),
                                    ("Отступом", False),
                                    ("Словом begin", False),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "Функции и структуры",
                "order": 2,
                "skill": "js-functions",
                "lessons": [
                    {
                        "title": "Функции",
                        "content": (
                            "## Функции\n\n"
                            "```javascript\n"
                            "function greet(name) {\n"
                            '  return "Привет, " + name;\n'
                            "}\n\n"
                            'console.log(greet("Ада"));\n'
                            "```\n\n"
                            "### Стрелочные функции\n\n"
                            "Короткая запись:\n\n"
                            "```javascript\n"
                            "const add = (a, b) => a + b;\n"
                            "console.log(add(2, 3));  // 5\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Какое ключевое слово объявляет функцию?",
                                "choices": [("function", True), ("def", False), ("fun", False)],
                            },
                            {
                                "text": "Что возвращает значение из функции?",
                                "choices": [("return", True), ("print", False), ("give", False)],
                            },
                        ],
                    },
                    {
                        "title": "Массивы",
                        "content": (
                            "## Массивы\n\n"
                            "```javascript\n"
                            "const fruits = ['яблоко', 'банан', 'вишня'];\n"
                            "console.log(fruits[0]);      // яблоко\n"
                            "console.log(fruits.length);  // 3\n"
                            "```\n\n"
                            "Индексация с **0**. Методы:\n\n"
                            "```javascript\n"
                            "fruits.push('груша');   // добавить в конец\n"
                            "fruits.forEach(f => console.log(f));\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "С какого индекса начинается нумерация массива?",
                                "choices": [("С 0", True), ("С 1", False), ("С -1", False)],
                            },
                            {
                                "text": "Как добавить элемент в конец массива?",
                                "choices": [
                                    (".push()", True),
                                    (".append()", False),
                                    (".add()", False),
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Объекты",
                        "content": (
                            "## Объекты\n\n"
                            "Объект хранит пары «ключ — значение»:\n\n"
                            "```javascript\n"
                            "const user = {\n"
                            '  name: "Ада",\n'
                            "  age: 36\n"
                            "};\n\n"
                            "console.log(user.name);   // Ада\n"
                            "console.log(user['age']);  // 36\n"
                            "```\n\n"
                            'Свойства можно менять и добавлять: `user.city = "Лондон";`\n'
                        ),
                        "questions": [
                            {
                                "text": "Как обратиться к свойству name у объекта user?",
                                "choices": [
                                    ("user.name", True),
                                    ("user->name", False),
                                    ("user::name", False),
                                ],
                            },
                            {
                                "text": "Как записываются пары ключ-значение в объекте?",
                                "choices": [
                                    ("ключ: значение", True),
                                    ("ключ = значение", False),
                                    ("ключ => значение", False),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "DOM и события",
                "order": 3,
                "skill": "js-dom",
                "lessons": [
                    {
                        "title": "Работа с DOM",
                        "content": (
                            "## Что такое DOM\n\n"
                            "**DOM** — представление HTML-страницы, которым управляет JS.\n\n"
                            "```javascript\n"
                            "const title = document.querySelector('h1');\n"
                            "title.textContent = 'Новый заголовок';\n"
                            "```\n\n"
                            "### События\n\n"
                            "```javascript\n"
                            "const btn = document.querySelector('button');\n"
                            "btn.addEventListener('click', () => {\n"
                            "  alert('Клик!');\n"
                            "});\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Каким методом находят первый элемент по селектору?",
                                "choices": [
                                    ("document.querySelector()", True),
                                    ("document.getElement()", False),
                                    ("document.find()", False),
                                ],
                            },
                            {
                                "text": "Как подписаться на клик по кнопке?",
                                "choices": [
                                    ("addEventListener('click', ...)", True),
                                    ("onClick(...)", False),
                                    ("listen('click')", False),
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },
    # ---------------------------------------------------------------------- C#
    {
        "title": "C#",
        "icon": "🟪",
        "cover": "csharp.png",
        "description": (
            "Основы C# и платформы .NET: переменные, управляющие конструкции, коллекции "
            "и объектно-ориентированное программирование."
        ),
        "sections": [
            {
                "title": "Основы C#",
                "order": 1,
                "skill": "cs-basics",
                "lessons": [
                    {
                        "title": "Введение и вывод",
                        "content": (
                            "## Что такое C#?\n\n"
                            "**C#** — современный объектно-ориентированный язык от Microsoft, "
                            "работает на платформе **.NET**.\n\n"
                            "Минимальная программа:\n\n"
                            "```csharp\n"
                            "using System;\n\n"
                            "class Program\n"
                            "{\n"
                            "    static void Main()\n"
                            "    {\n"
                            '        Console.WriteLine("Привет, мир!");\n'
                            "    }\n"
                            "}\n"
                            "```\n\n"
                            "`Console.WriteLine` выводит строку и переносит курсор.\n"
                        ),
                        "questions": [
                            {
                                "text": "Какая команда выводит строку в консоль?",
                                "choices": [
                                    ("Console.WriteLine()", True),
                                    ("print()", False),
                                    ("echo()", False),
                                ],
                            },
                            {
                                "text": "Напишите имя класса с точкой входа Main (без скобок)",
                                "kind": "text",
                                "answer_text": "Program|program",
                            },
                        ],
                    },
                    {
                        "title": "Переменные и типы",
                        "content": (
                            "## Переменные\n\n"
                            "```csharp\n"
                            "int age = 36;\n"
                            "double height = 1.7;\n"
                            'string name = "Ада";\n'
                            "bool isStudent = true;\n"
                            "```\n\n"
                            "Тип можно не писать — `var` выведет его сам:\n\n"
                            "```csharp\n"
                            'var city = "Лондон";  // string\n'
                            "```\n\n"
                            "Основные типы: `int`, `double`, `string`, `bool`.\n"
                        ),
                        "questions": [
                            {
                                "text": "Какой тип у 3.14 в C#?",
                                "choices": [("double", True), ("int", False), ("float", False)],
                            },
                            {
                                "text": "Каким словом объявить переменную с авто-выводом типа?",
                                "choices": [("var", True), ("let", False), ("auto", False)],
                            },
                        ],
                    },
                    {
                        "title": "Условия",
                        "content": (
                            "## if / else\n\n"
                            "```csharp\n"
                            "int score = 75;\n"
                            "if (score >= 90)\n"
                            '    Console.WriteLine("5");\n'
                            "else if (score >= 70)\n"
                            '    Console.WriteLine("4");\n'
                            "else\n"
                            '    Console.WriteLine("3");\n'
                            "```\n\n"
                            "### switch\n\n"
                            "```csharp\n"
                            "switch (day)\n"
                            "{\n"
                            '    case 1: Console.WriteLine("Пн"); break;\n'
                            '    default: Console.WriteLine("?"); break;\n'
                            "}\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Чем выделяют блок if в C#?",
                                "choices": [
                                    ("Фигурными скобками {}", True),
                                    ("Отступом", False),
                                    ("Словом start", False),
                                ],
                            },
                            {
                                "text": "Как обозначается проверка на равенство?",
                                "choices": [("==", True), ("=", False), ("===", False)],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "Циклы и коллекции",
                "order": 2,
                "skill": "cs-collections",
                "lessons": [
                    {
                        "title": "Циклы",
                        "content": (
                            "## for, while, foreach\n\n"
                            "```csharp\n"
                            "for (int i = 0; i < 5; i++)\n"
                            "    Console.WriteLine(i);\n\n"
                            "int n = 3;\n"
                            "while (n > 0)\n"
                            "{\n"
                            "    Console.WriteLine(n);\n"
                            "    n--;\n"
                            "}\n"
                            "```\n\n"
                            "`foreach` перебирает элементы коллекции:\n\n"
                            "```csharp\n"
                            "foreach (var item in new[] { 1, 2, 3 })\n"
                            "    Console.WriteLine(item);\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Какой цикл перебирает элементы коллекции?",
                                "choices": [("foreach", True), ("forin", False), ("loop", False)],
                            },
                            {
                                "text": "Что делает оператор i++ ?",
                                "choices": [
                                    ("Увеличивает i на 1", True),
                                    ("Уменьшает i на 1", False),
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Массивы и List",
                        "content": (
                            "## Массивы\n\n"
                            "```csharp\n"
                            'string[] fruits = { "яблоко", "банан" };\n'
                            "Console.WriteLine(fruits[0]);      // яблоко\n"
                            "Console.WriteLine(fruits.Length);  // 2\n"
                            "```\n\n"
                            "## List — динамический список\n\n"
                            "```csharp\n"
                            "using System.Collections.Generic;\n\n"
                            "var list = new List<int>();\n"
                            "list.Add(10);\n"
                            "list.Add(20);\n"
                            "Console.WriteLine(list.Count);  // 2\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Как узнать длину массива в C#?",
                                "choices": [
                                    (".Length", True),
                                    (".length", False),
                                    (".size", False),
                                ],
                            },
                            {
                                "text": "Как добавить элемент в List?",
                                "choices": [
                                    (".Add()", True),
                                    (".push()", False),
                                    (".append()", False),
                                ],
                            },
                        ],
                    },
                    {
                        "title": "Методы",
                        "content": (
                            "## Методы\n\n"
                            "**Метод** — именованный блок кода внутри класса.\n\n"
                            "```csharp\n"
                            "class Program\n"
                            "{\n"
                            "    static int Add(int a, int b)\n"
                            "    {\n"
                            "        return a + b;\n"
                            "    }\n\n"
                            "    static void Main()\n"
                            "    {\n"
                            "        Console.WriteLine(Add(2, 3));  // 5\n"
                            "    }\n"
                            "}\n"
                            "```\n\n"
                            "`static` — метод принадлежит классу, а не объекту. "
                            "`return` возвращает результат.\n"
                        ),
                        "questions": [
                            {
                                "text": "Что возвращает значение из метода?",
                                "choices": [("return", True), ("print", False), ("out", False)],
                            },
                            {
                                "text": "Что означает модификатор static у метода?",
                                "choices": [
                                    ("Метод принадлежит классу, а не объекту", True),
                                    ("Метод нельзя вызвать", False),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "ООП в C#",
                "order": 3,
                "skill": "cs-oop",
                "lessons": [
                    {
                        "title": "Классы и объекты",
                        "content": (
                            "## Классы\n\n"
                            "**Класс** — шаблон, **объект** — его экземпляр.\n\n"
                            "```csharp\n"
                            "class Dog\n"
                            "{\n"
                            "    public string Name;\n\n"
                            "    public void Bark()\n"
                            "    {\n"
                            '        Console.WriteLine(Name + " говорит: Гав!");\n'
                            "    }\n"
                            "}\n\n"
                            "var dog = new Dog();\n"
                            'dog.Name = "Рекс";\n'
                            "dog.Bark();\n"
                            "```\n\n"
                            "Поле `Name` хранит состояние, метод `Bark` — поведение.\n"
                        ),
                        "questions": [
                            {
                                "text": "Каким словом создаётся объект класса в C#?",
                                "choices": [("new", True), ("create", False), ("make", False)],
                            },
                            {
                                "text": "Что такое класс?",
                                "choices": [
                                    ("Шаблон для создания объектов", True),
                                    ("Готовая переменная", False),
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },
    # --------------------------------------------------------------------- Java
    {
        "title": "Java",
        "icon": "☕",
        "cover": "java.png",
        "description": (
            "Основы Java: вывод, типы данных, условия, циклы, массивы, методы и классы. "
            "Один из самых востребованных языков для серверной разработки."
        ),
        "sections": [
            {
                "title": "Основы Java",
                "order": 1,
                "skill": "java-basics",
                "lessons": [
                    {
                        "title": "Введение и вывод",
                        "content": (
                            "## Что такое Java?\n\n"
                            "**Java** — строго типизированный объектно-ориентированный язык, "
                            "работающий на виртуальной машине **JVM**.\n\n"
                            "Минимальная программа:\n\n"
                            "```java\n"
                            "public class Main {\n"
                            "    public static void main(String[] args) {\n"
                            '        System.out.println("Привет, мир!");\n'
                            "    }\n"
                            "}\n"
                            "```\n\n"
                            "Точка входа — метод `main`.\n"
                        ),
                        "questions": [
                            {
                                "text": "Какой метод выводит строку в Java?",
                                "choices": [
                                    ("System.out.println()", True),
                                    ("print()", False),
                                    ("console.log()", False),
                                ],
                            },
                            {
                                "text": "Как называется точка входа в программу на Java?",
                                "choices": [("main", True), ("start", False), ("run", False)],
                            },
                        ],
                    },
                    {
                        "title": "Переменные и типы",
                        "content": (
                            "## Переменные\n\n"
                            "Java требует указывать тип:\n\n"
                            "```java\n"
                            "int age = 36;\n"
                            "double height = 1.7;\n"
                            'String name = "Ада";\n'
                            "boolean isStudent = true;\n"
                            "```\n\n"
                            "Основные типы: `int`, `double`, `boolean`, а `String` — это класс.\n"
                        ),
                        "questions": [
                            {
                                "text": "Какой тип у 3.14 в Java?",
                                "choices": [("double", True), ("int", False), ("float", False)],
                            },
                            {
                                "text": "Какой тип хранит true/false?",
                                "choices": [("boolean", True), ("bool", False), ("bit", False)],
                            },
                        ],
                    },
                    {
                        "title": "Условия",
                        "content": (
                            "## if / else\n\n"
                            "```java\n"
                            "int score = 75;\n"
                            "if (score >= 90) {\n"
                            '    System.out.println("5");\n'
                            "} else if (score >= 70) {\n"
                            '    System.out.println("4");\n'
                            "} else {\n"
                            '    System.out.println("3");\n'
                            "}\n"
                            "```\n\n"
                            "Проверка на равенство — `==`, для строк используют `.equals()`.\n"
                        ),
                        "questions": [
                            {
                                "text": "Как сравнивают строки в Java?",
                                "choices": [
                                    ("Методом .equals()", True),
                                    ("Оператором ==", False),
                                    ("Оператором ===", False),
                                ],
                            },
                            {
                                "text": "Чем выделяют блок if в Java?",
                                "choices": [
                                    ("Фигурными скобками {}", True),
                                    ("Отступом", False),
                                ],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "Циклы и массивы",
                "order": 2,
                "skill": "java-collections",
                "lessons": [
                    {
                        "title": "Циклы",
                        "content": (
                            "## for, while, for-each\n\n"
                            "```java\n"
                            "for (int i = 0; i < 5; i++) {\n"
                            "    System.out.println(i);\n"
                            "}\n\n"
                            "int n = 3;\n"
                            "while (n > 0) {\n"
                            "    System.out.println(n);\n"
                            "    n--;\n"
                            "}\n"
                            "```\n\n"
                            "Улучшенный `for` перебирает элементы массива:\n\n"
                            "```java\n"
                            "int[] nums = {1, 2, 3};\n"
                            "for (int x : nums) System.out.println(x);\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Какой цикл перебирает элементы массива без индекса?",
                                "choices": [
                                    ("for (int x : nums)", True),
                                    ("foreach (x in nums)", False),
                                    ("loop nums", False),
                                ],
                            },
                            {
                                "text": "Сколько раз выполнится for (int i = 0; i < 5; i++) ?",
                                "choices": [("5", True), ("4", False), ("6", False)],
                            },
                        ],
                    },
                    {
                        "title": "Массивы",
                        "content": (
                            "## Массивы\n\n"
                            "```java\n"
                            "int[] numbers = {10, 20, 30};\n"
                            "System.out.println(numbers[0]);      // 10\n"
                            "System.out.println(numbers.length);  // 3\n"
                            "```\n\n"
                            "Индексация с **0**. Длину массива даёт поле `length` (без скобок).\n\n"
                            "```java\n"
                            "int[] empty = new int[5];  // массив из 5 нулей\n"
                            "```\n"
                        ),
                        "questions": [
                            {
                                "text": "Как узнать длину массива в Java?",
                                "choices": [
                                    (".length", True),
                                    (".length()", False),
                                    (".size()", False),
                                ],
                            },
                            {
                                "text": "С какого индекса начинается нумерация массива?",
                                "choices": [("С 0", True), ("С 1", False), ("С -1", False)],
                            },
                        ],
                    },
                    {
                        "title": "Методы",
                        "content": (
                            "## Методы\n\n"
                            "```java\n"
                            "public class Main {\n"
                            "    static int add(int a, int b) {\n"
                            "        return a + b;\n"
                            "    }\n\n"
                            "    public static void main(String[] args) {\n"
                            "        System.out.println(add(2, 3));  // 5\n"
                            "    }\n"
                            "}\n"
                            "```\n\n"
                            "`static` — метод принадлежит классу. `return` возвращает результат, "
                            "`void` — метод ничего не возвращает.\n"
                        ),
                        "questions": [
                            {
                                "text": "Что означает return-тип void?",
                                "choices": [
                                    ("Метод ничего не возвращает", True),
                                    ("Метод возвращает 0", False),
                                ],
                            },
                            {
                                "text": "Что возвращает значение из метода?",
                                "choices": [("return", True), ("print", False), ("out", False)],
                            },
                        ],
                    },
                ],
            },
            {
                "title": "ООП в Java",
                "order": 3,
                "skill": "java-oop",
                "lessons": [
                    {
                        "title": "Классы и объекты",
                        "content": (
                            "## Классы\n\n"
                            "```java\n"
                            "class Dog {\n"
                            "    String name;\n\n"
                            "    void bark() {\n"
                            '        System.out.println(name + " говорит: Гав!");\n'
                            "    }\n"
                            "}\n\n"
                            "public class Main {\n"
                            "    public static void main(String[] args) {\n"
                            "        Dog dog = new Dog();\n"
                            '        dog.name = "Рекс";\n'
                            "        dog.bark();\n"
                            "    }\n"
                            "}\n"
                            "```\n\n"
                            "`new` создаёт объект класса `Dog`.\n"
                        ),
                        "questions": [
                            {
                                "text": "Каким словом создаётся объект класса в Java?",
                                "choices": [("new", True), ("create", False), ("make", False)],
                            },
                            {
                                "text": "Что такое объект?",
                                "choices": [
                                    ("Экземпляр класса", True),
                                    ("Шаблон класса", False),
                                ],
                            },
                        ],
                    },
                ],
            },
        ],
    },
]


class Command(BaseCommand):
    help = "Создаёт демонстрационные данные: 4 курса (Python, JavaScript, C#, Java)."

    @transaction.atomic
    def handle(self, *args, **options):
        services.seed_achievements()
        skills = self._seed_skills()
        self.stdout.write(self.style.SUCCESS("Достижения и навыки созданы."))

        self._user("admin", "admin@example.com", "admin12345", User.Role.ADMIN, True, True)
        teacher = self._user("teacher", "teacher@example.com", "teacher12345", User.Role.TEACHER)
        self._user("student", "student@example.com", "student12345", User.Role.STUDENT)

        # Чистим прежние курсы, чтобы структура обновилась.
        Course.objects.filter(title__in=LEGACY_TITLES).delete()

        for course_data in COURSES:
            self._create_course(teacher, course_data, skills)

        total_lessons = sum(
            len(section["lessons"]) for course in COURSES for section in course["sections"]
        )
        self.stdout.write(
            self.style.SUCCESS(
                f"Готово: {len(COURSES)} курса, {total_lessons} уроков, {len(SKILLS)} навыков.\n"
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

    def _create_course(self, teacher, data, skills):
        course = Course.objects.create(
            title=data["title"],
            description=data["description"],
            owner=teacher,
            is_published=True,
            cover=data.get("cover", ""),
            icon=data.get("icon", "📘"),
        )
        for section_data in data["sections"]:
            self._create_section(course, teacher, section_data, skills)
        return course

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
            question = Question.objects.create(
                test=test,
                text=q["text"],
                kind=q.get("kind", Question.Kind.CHOICE),
                answer_text=q.get("answer_text", ""),
                order=order,
            )
            for choice_text, is_correct in q.get("choices", []):
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
