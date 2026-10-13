# Архитектура дипломного проекта — Платформа самообучения «Эрудит» (Erudite LMS)

> Название проекта: **Erudite / Эрудит** — платформа самообучения
> Альтернативы: `SkillBridge`, `LearnHub`, `Горизонт`, `Квант`

## 1. Стек и обоснование

| Слой | Технология | Почему |
|------|------------|--------|
| Backend | **Django 5 + Django REST Framework** | Требование ТЗ, быстрая разработка, готовая админка |
| Auth | **djangorestframework-simplejwt** | JWT access/refresh, требование ТЗ |
| DB | **PostgreSQL 15+** | Требование ТЗ, JSONB, надёжность |
| ORM | **Django ORM** | Требование ТЗ |
| Docs | **drf-spectacular** (OpenAPI 3 + Swagger UI) | Современная замена drf-yasg, автогенерация схемы |
| CORS | **django-cors-headers** | Требование ТЗ |
| Code quality | **black, isort, flake8, mypy** | PEP8 |
| Testing | **pytest + pytest-django + factory-boy + coverage** | Покрытие всех основных функций |
| Deploy | **Docker + docker-compose + gunicorn + .env** | Воспроизводимость |
| VCS | **Git + GitHub** | Требование ТЗ |

Архитектура — **монолит модульный** (рекомендуется для диплома). Каждый домен — отдельное Django-приложение. Это проще защищать, чем микросервисы, и полностью покрывает ТЗ.

## 2. Высокоуровневая архитектура

```
[ Client (Browser / SPA / Mobile) ]
        |  HTTPS + JWT (Authorization: Bearer <access>)
        v
[ Nginx / Gunicorn ] -> [ Django + DRF ]
        |                    |-> users (Auth, JWT, Roles)
        |                    |-> courses (Курсы/Разделы)
        |                    |-> materials (Материалы)
        |                    |-> testing (Тесты, Вопросы, Ответы, Проверка)
        v
[ PostgreSQL ]  +  [ Django Admin ]  +  [ Swagger UI / Redoc ]
```

## 3. Приложения (apps)

Рекомендуемая структура проекта:

```
Erudite/
├── config/                 # настройки проекта (settings, urls, wsgi, asgi)
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── apps/
│   ├── users/              # Пользователи, регистрация, JWT, роли
│   ├── courses/            # Курсы и Разделы (Sections)
│   └── materials/          # Материалы + Тесты (или apps/testing отдельно)
│   └── testing/            # (альтернатива) Тесты вынесены отдельно
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
├── .gitignore
├── pytest.ini
└── README.md
```

### 3.1 `apps.users`
Отвечает за всё, что связано с пользователем.

**Модель User (наследник AbstractUser):**
```python
class User(AbstractUser):
    class Role(models.TextChoices):
        ADMIN = "admin", "Администратор"
        TEACHER = "teacher", "Преподаватель"
        STUDENT = "student", "Студент"
    email = EmailField(unique=True) # LOGIN = email
    role = CharField(choices=Role, default=Role.STUDENT)
    avatar = ImageField(null=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]
```

**Эндпоинты:**
- `POST /api/auth/register/` — регистрация
- `POST /api/auth/login/` — получение пары JWT (simplejwt)
- `POST /api/auth/token/refresh/` — обновление access
- `GET /api/users/me/` — профиль
- `GET /api/users/` — только для admin

### 3.2 `apps.courses` — Курсы и Разделы
Сущность `Курс` — владелец (teacher). Внутри курса — разделы.

```python
class Course(models.Model):
    title = CharField(max_length=255)
    description = TextField()
    owner = ForeignKey(User, on_delete=CASCADE, related_name="courses")
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)

class Section(models.Model):
    course = ForeignKey(Course, on_delete=CASCADE, related_name="sections")
    title = CharField(max_length=255)
    description = TextField(blank=True)
    order = PositiveIntegerField(default=0)
    class Meta: ordering = ["order"]
```

### 3.3 `apps.materials` — Материалы
Каждый материал принадлежит разделу.

```python
class Material(models.Model):
    section = ForeignKey(Section, on_delete=CASCADE, related_name="materials")
    title = CharField(max_length=255)
    content = TextField() # текст/ markdown
    video_url = URLField(blank=True)
    owner = ForeignKey(User, on_delete=CASCADE) # денормализация для пермишенов
    created_at = DateTimeField(auto_now_add=True)
```

### 3.4 `apps.testing` — Тестирование знаний
Классический вариант: Тест -> Вопросы -> Варианты ответа.

```python
class Test(models.Model):
    material = ForeignKey(Material, on_delete=CASCADE, related_name="tests") # или OneToOne
    title = CharField(max_length=255)
    description = TextField(blank=True)
    owner = ForeignKey(User, on_delete=CASCADE)

class Question(models.Model):
    test = ForeignKey(Test, on_delete=CASCADE, related_name="questions")
    text = TextField()
    order = PositiveIntegerField(default=0)

class Choice(models.Model):
    question = ForeignKey(Question, on_delete=CASCADE, related_name="choices")
    text = CharField(max_length=500)
    is_correct = BooleanField(default=False) # скрываем от студента в сериализаторе

class TestSubmission(models.Model):
    test = ForeignKey(Test, on_delete=CASCADE)
    user = ForeignKey(User, on_delete=CASCADE)
    score = IntegerField()
    total = IntegerField()
    is_passed = BooleanField()
    created_at = DateTimeField(auto_now_add=True)

class SubmissionAnswer(models.Model):
    submission = ForeignKey(TestSubmission, on_delete=CASCADE, related_name="answers")
    question = ForeignKey(Question, on_delete=CASCADE)
    selected_choices = ManyToManyField(Choice)
```

> **Ключевое требование ТЗ:** проверка через отдельный запрос. 
> `POST /api/tests/{id}/submit/` принимает `{answers: [{question_id, choice_ids}]}` и возвращает `{score, total, passed, details}`. Поле `is_correct` никогда не отдаётся в GET теста для студентов.

## 4. ER-диаграмма (упрощённо)

```
User 1--* Course 1--* Section 1--* Material 1--* Test 1--* Question 1--* Choice
                                      |                 |
                                      |                 *--* TestSubmission --* SubmissionAnswer
                                      |                         |
                                      User *---------------------*
```

## 5. Система прав (RBAC)

Матрица доступа:

| Действие | Admin | Teacher (владелец) | Teacher (чужой курс) | Student | Гость |
|---|---|---|---|---|---|
| CRUD пользователи | + | - | - | - | - |
| CRUD любой курс/раздел/материал/тест | + | - | - | - | - |
| CRUD свой курс/раздел/материал/тест | + | + | - | - | - |
| Просмотр материалов | + | + | + | + | - |
| Прохождение теста (submit) | - | - | - | + | - |
| Просмотр чужих результатов | + | + (свои тесты) | - | - | - |

**Реализация:**
- `IsAuthenticated` + `JWTAuthentication` глобально
- Кастомные пермишены: `IsAdmin`, `IsTeacher`, `IsOwnerOrAdmin`, `IsStudent`
- В `ViewSet.get_permissions()` и `get_queryset()` — фильтрация по `owner` / `role`
- Для студента сериализатор теста исключает `is_correct`

Пример:
```python
class IsOwnerOrAdmin(BasePermission):
    def has_object_permission(self, request, view, obj):
        return request.user.is_staff or request.user.role == "admin" or obj.owner == request.user
```

## 6. API дизайн (REST)

```
/api/auth/register/          POST
/api/auth/token/             POST  (login)
/api/auth/token/refresh/     POST
/api/auth/token/verify/      POST

/api/courses/                GET, POST
/api/courses/{id}/           GET, PUT, PATCH, DELETE
/api/courses/{id}/sections/  GET, POST

/api/sections/{id}/          GET, PUT, PATCH, DELETE
/api/sections/{id}/materials/ GET, POST

/api/materials/{id}/         GET, PUT, PATCH, DELETE
/api/materials/{id}/tests/   GET, POST

/api/tests/{id}/             GET, PUT, PATCH, DELETE
/api/tests/{id}/questions/   GET, POST
/api/tests/{id}/submit/      POST  ← проверка ответов (требование ТЗ)

/api/docs/                   Swagger UI
/api/schema/                 OpenAPI JSON
/api/redoc/                  Redoc
/admin/                      Django Admin
```

Все ViewSet — `ModelViewSet` с `IsAuthenticated`, пагинацией, фильтрами (`django-filter`), поиском.

## 7. Безопасность и настройки

- `SIMPLE_JWT = {ACCESS 60min, REFRESH 7d, ROTATE...}`
- `CORS_ALLOWED_ORIGINS = env.list(...)` или `CORS_ALLOW_ALL_ORIGINS=False`
- `AUTH_USER_MODEL = "users.User"`
- Пароли — `PBKDF2`, валидаторы Django
- `DEFAULT_AUTHENTICATION_CLASSES = (JWTAuthentication,)`
- Throttling для `/submit/` и `/token/`

## 8. Админка
Все модели регистрируются в `admin.py` с `list_display`, `list_filter`, `search_fields`, `inlines` (QuestionInline в TestAdmin, ChoiceInline в QuestionAdmin).

## 9. Тестирование
- `tests/test_auth.py` — регистрация, логин, JWT, доступ без токена 401
- `tests/test_courses.py` — CRUD, права владельца/чужого
- `tests/test_materials.py`
- `tests/test_testing.py` — создание теста, скрытие is_correct, submit с подсчётом баллов
- `tests/test_permissions.py` — матрица ролей
- Coverage >80%

## 10. Структура файлов (финальная)

```
Diplom_project/
├── config/
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   ├── wsgi.py
│   └── asgi.py
├── apps/
│   ├── users/
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── views.py
│   │   ├── permissions.py
│   │   ├── urls.py
│   │   ├── admin.py
│   │   └── tests.py
│   ├── courses/
│   └── testing/  (или materials/testing)
├── manage.py
├── requirements.txt
├── .env
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
├── pytest.ini
├── README.md
└── ARCHITECTURE.md
```

## 11. Почему эта архитектура идеально подходит под ТЗ

1. Закрывает все 4 блока требований (Auth, Контент, Тесты, Права) отдельными приложениями
2. CRUD через Admin + REST API из коробки
3. Проверка тестов отдельным запросом — честная серверная валидация
4. Роли реализованы одним полем + пермишенами — просто и расширяемо
5. Легко писать тесты и генерировать Swagger
6. Монолит проще деплоить и защищать на дипломе
