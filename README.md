# Erudite LMS — платформа самообучения

Дипломный проект: REST API платформа для самообучения студентов на **Django + Django REST Framework**.
Поддерживает авторизацию по JWT, управление курсами/разделами/материалами, тестирование знаний
с серверной проверкой ответов и ролевую модель доступа (админ / преподаватель / студент).

## Стек

- Python 3.12+, Django 5, Django REST Framework
- PostgreSQL (в dev можно SQLite)
- JWT — `djangorestframework-simplejwt`
- Swagger/OpenAPI — `drf-spectacular`
- CORS — `django-cors-headers`
- Фильтрация — `django-filter`
- Тесты — `pytest-django`, `factory-boy`
- Docker / docker-compose

## Структура проекта

```
Diplom_project/
├── config/                 # настройки, urls, wsgi/asgi
├── apps/
│   ├── users/              # User(role), регистрация, JWT, профиль, права
│   ├── courses/            # Course -> Section
│   ├── materials/          # Material
│   └── testing/            # Test -> Question -> Choice, TestSubmission
├── conftest.py             # общие pytest-фикстуры (пользователи, JWT-клиенты)
├── pytest.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── ARCHITECTURE.md         # описание архитектуры и ER-модели
```

## Роли

| Роль | Возможности |
|------|-------------|
| **admin** | полный доступ ко всем объектам и пользователям, Django-админка |
| **teacher** | CRUD своих курсов/разделов/материалов/тестов, просмотр результатов |
| **student** | просмотр опубликованных материалов, прохождение тестов, свои результаты |

## Быстрый старт (локально, SQLite)

```bash
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/macOS

pip install -r requirements.txt
copy .env.example .env          # Windows (cp на Linux) — по умолчанию SQLite
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

- Swagger UI: http://127.0.0.1:8000/api/docs/
- ReDoc: http://127.0.0.1:8000/api/redoc/
- Django Admin: http://127.0.0.1:8000/admin/

## Запуск с PostgreSQL

В `.env` укажите:

```
DB_ENGINE=django.db.backends.postgresql
DB_NAME=erudite
DB_USER=postgres
DB_PASSWORD=postgres
DB_HOST=127.0.0.1
DB_PORT=5432
```

## Запуск через Docker

```bash
docker compose up --build
```

Поднимает PostgreSQL и web (gunicorn) на порту 8000.

## API (кратко)

### Аутентификация
| Метод | URL | Описание |
|-------|-----|----------|
| POST | `/api/auth/register/` | регистрация |
| POST | `/api/auth/token/` | вход → `access`/`refresh` |
| POST | `/api/auth/token/refresh/` | обновление access |
| POST | `/api/auth/token/verify/` | проверка токена |
| GET/PATCH | `/api/users/me/` | профиль |
| GET | `/api/users/` | список (admin) |

### Контент
| Метод | URL |
|-------|-----|
| CRUD | `/api/courses/` , `/api/sections/` , `/api/materials/` |
| CRUD | `/api/tests/` |

Поддерживаются фильтры (`?course=`, `?section=`, `?material=`), поиск (`?search=`) и пагинация (`?page=`).

### Проверка знаний
```http
POST /api/tests/{id}/submit/
Authorization: Bearer <access>

{
  "answers": [
    {"question": 1, "choices": [3]}
  ]
}
```
Ответ:
```json
{
  "submission_id": 5, "score": 1, "total": 1,
  "percentage": 100.0, "is_passed": true, "passing_score": 60,
  "details": [
    {"question": 1, "is_correct": true,
     "selected_choices": [3], "correct_choices": [3]}
  ]
}
```

- `GET /api/tests/{id}/results/` — результаты теста (владелец/админ)
- `GET /api/tests/my-results/` — результаты текущего студента

Правильные ответы (`is_correct`) **никогда** не отдаются студенту в GET теста.

## Тестирование

```bash
pytest
pytest --cov=apps --cov-report=term-missing
```

## Качество кода

```bash
black .
isort .
flake8
```
