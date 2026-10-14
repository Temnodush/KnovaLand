# KnovaLand — платформа самообучения с геймификацией

Дипломный проект: платформа для самообучения на **Django + Django REST Framework**.
Поддерживает авторизацию по JWT, управление курсами/разделами/материалами, тестирование знаний
с серверной проверкой ответов, ролевую модель доступа (админ / преподаватель / студент)
и **геймификацию**: опыт (XP), уровни, достижения, прогрессия по курсам и рейтинг игроков.
Плюс геймифицированный веб-интерфейс на **Django Templates + HTMX + Tailwind** поверх того же API.

## Стек

- Python 3.12+, Django 5, Django REST Framework
- PostgreSQL (в dev можно SQLite)
- JWT — `djangorestframework-simplejwt`
- Swagger/OpenAPI — `drf-spectacular`
- CORS — `django-cors-headers`
- Фильтрация — `django-filter`
- Frontend — Django Templates + HTMX + Tailwind CSS (серверный рендеринг, без сборки)
- Тесты — `pytest-django`, `factory-boy`
- Docker / docker-compose

## Структура проекта

```
Diplom_project/
├── config/                 # настройки, urls, wsgi/asgi
├── apps/
│   ├── users/              # User(role), регистрация, JWT, профиль, права, вход по email/логину
│   ├── courses/            # Course -> Section
│   ├── materials/          # Material
│   ├── testing/            # Test -> Question -> Choice, TestSubmission
│   ├── gamification/       # XP, уровни, достижения, зачисления, прогресс, рейтинг
│   └── web/                # геймифицированный веб-интерфейс (HTMX + Tailwind)
├── templates/              # base.html и страницы (dashboard, course_detail, leaderboard, profile)
├── static/                 # css
├── conftest.py             # общие pytest-фикстуры (пользователи, JWT-клиенты)
├── pytest.ini
├── requirements.txt
├── Dockerfile
├── docker-compose.yml
├── .env.example
└── ARCHITECTURE.md         # описание архитектуры и ER-модели
```

## Геймификация

| Механика | Реализация |
|----------|------------|
| **Опыт (XP)** | +10 за материал, +10 за запись на курс, за тест: `10 + 10 × правильных` |
| **Уровень** | от накопленного XP (ур. 2 — 100 XP, ур. 3 — 300 XP, ур. 4 — 600 XP …) |
| **Достижения** | «Первый шаг», «Первое испытание», «Без единой ошибки», «Неделя силы» и др. |
| **Прогрессия** | процент прохождения курса, автозавершение при 100% |
| **Серия дней** | ежедневная серия занятий (streak) |
| **Рейтинг** | топ игроков по опыту |

Логика в `apps/gamification/services.py`, начисление — через сигналы на `TestSubmission`,
`MaterialProgress` и `Enrollment` (`apps/gamification/signals.py`).

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
DB_NAME=knova
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

### Геймификация
| Метод | URL | Описание |
|-------|-----|----------|
| GET | `/api/game/profile/` | игровой профиль (XP, уровень, серия, достижения) |
| GET | `/api/game/leaderboard/` | рейтинг по опыту (`?course=<id>`) |
| GET | `/api/game/achievements/` | список достижений и статус получения |
| GET | `/api/game/enrollments/` | мои курсы |
| POST | `/api/game/enroll/` | записаться на курс (`{"course": 1}`) |
| POST | `/api/game/progress/` | отметить материал пройденным (`{"material": 1}`) |

## Веб-интерфейс (Django + HTMX + Tailwind)

Геймифицированный UI поверх того же бэкенда, аутентификация — через сессию Django:

| Страница | URL | Описание |
|----------|-----|----------|
| Главная | `/` | витрина курсов |
| Регистрация | `/register/` | регистрация студента/преподавателя + письмо подтверждения email |
| Подтверждение email | `/verify-email/<token>/` | ссылка из письма активирует `email_verified` |
| Повтор письма | `/verify-email/resend/` | отправить подтверждение ещё раз |
| Вход | `/login/` | вход по **email или логину** |
| Кабинет | `/dashboard/` | XP-бар, мои курсы с прогрессом, достижения |
| Карта курса | `/courses/<id>/` | разделы и материалы, кнопка «Пройти» (HTMX, +10 XP без перезагрузки) |
| Рейтинг | `/leaderboard/` | таблица лидеров |
| Профиль | `/profile/` | достижения и история начислений |

## Подтверждение email

- При регистрации (через веб или `POST /api/auth/register/`) создаётся пользователь и
  отправляется письмо со ссылкой вида `/verify-email/<token>/`.
- Токен — **подписанный** (`TimestampSigner`), действует 3 дня, хранить его в БД не нужно.
- Неподтверждённый пользователь видит баннер «Email не подтверждён» с кнопкой повторной отправки.
- По умолчанию вход **разрешён** и без подтверждения. Чтобы требовать подтверждение, поставьте
  `EMAIL_VERIFICATION_REQUIRED=True` в `.env`.
- Настройки SMTP — в `.env` (`EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`).
  Если учётка не задана, письма печатаются в консоль (удобно для разработки).


## Демо-данные

```bash
python manage.py seed_demo
```

Создаёт достижения, курсы («Основы Python», «Управление версиями с Git») и трёх пользователей:

| Логин | Пароль | Роль |
|-------|--------|------|
| `admin` | `admin12345` | администратор |
| `teacher` | `teacher12345` | преподаватель |
| `student` | `student12345` | студент |

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
