"""Серверные (не-API) представления для геймифицированного веб-интерфейса."""

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.courses.models import Course
from apps.gamification import services
from apps.gamification.models import (
    Achievement,
    Enrollment,
    MaterialProgress,
    PlayerAchievement,
    Skill,
)
from apps.materials.models import Material
from apps.testing.services import grade_test
from apps.users.emails import try_send_verification_email
from apps.users.forms import WebRegisterForm
from apps.users.tokens import read_email_verification_token

User = get_user_model()


def _profile(user):
    return services.get_profile(user)


def register(request):
    """Регистрация с подтверждением email."""
    if request.user.is_authenticated:
        return redirect("web:dashboard")
    if request.method == "POST":
        form = WebRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            sent = try_send_verification_email(request, user)
            if sent:
                messages.success(
                    request,
                    f"Регистрация прошла успешно! Мы отправили письмо с подтверждением "
                    f"на {user.email}. Проверьте почту.",
                )
            else:
                messages.warning(
                    request,
                    "Регистрация прошла, но письмо не удалось отправить. "
                    "Войдите и запросите письмо повторно.",
                )
            return redirect("web:login")
    else:
        form = WebRegisterForm()
    return render(request, "registration/register.html", {"form": form})


def verify_email(request, token):
    """Подтверждение email по ссылке из письма."""
    user_id = read_email_verification_token(token)
    user = User.objects.filter(pk=user_id).first() if user_id else None
    if user is None:
        messages.error(request, "Ссылка подтверждения недействительна или устарела.")
        return redirect("web:login")
    if user.email_verified:
        messages.info(request, "Email уже подтверждён — можно входить.")
        return redirect("web:login")
    user.email_verified = True
    user.save(update_fields=["email_verified"])
    messages.success(request, "Email подтверждён! Теперь войдите в аккаунт.")
    return redirect("web:login")


@login_required
@require_POST
def resend_verification(request):
    """Повторная отправка письма с подтверждением."""
    if request.user.email_verified:
        messages.info(request, "Ваш email уже подтверждён.")
        return redirect("web:dashboard")
    sent = try_send_verification_email(request, request.user)
    if sent:
        messages.success(request, f"Письмо повторно отправлено на {request.user.email}.")
    else:
        messages.error(request, "Не удалось отправить письмо. Попробуйте позже.")
    return redirect("web:dashboard")


def home(request):
    """Публичная главная: список доступных курсов."""
    courses = Course.objects.filter(is_published=True).select_related("owner")
    return render(request, "web/home.html", {"courses": courses})


@login_required
def dashboard(request):
    """Личный кабинет — сводка прогресса."""
    profile = _profile(request.user)
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .select_related("course")
        .order_by("-started_at")
    )
    enrolled_courses = []
    for enrollment in enrollments:
        enrolled_courses.append(
            {
                "course": enrollment.course,
                "enrollment": enrollment,
                "percent": services.course_progress_percent(request.user, enrollment.course),
                "completed": enrollment.is_completed,
            }
        )

    earned_ids = set(
        PlayerAchievement.objects.filter(profile=profile).values_list("achievement_id", flat=True)
    )
    achievements = Achievement.objects.all()
    skills = profile.skills.select_related("skill").all()

    available = (
        Course.objects.filter(is_published=True)
        .exclude(enrollments__user=request.user)
        .select_related("owner")[:6]
    )

    context = {
        "profile": profile,
        "enrolled_courses": enrolled_courses,
        "achievements": achievements,
        "earned_ids": earned_ids,
        "skills": skills,
        "available_courses": available,
    }
    return render(request, "web/dashboard.html", context)


def _course_structure(user, course):
    """Построить структуру курса: разделы → уроки с состоянием открытия/прохождения."""
    completed = services.completed_lesson_ids(user, course)
    sections = []
    for section in course.sections.order_by("order", "id").prefetch_related("materials"):
        lessons = []
        for lesson in section.materials.order_by("order", "id"):
            lessons.append(
                {
                    "obj": lesson,
                    "completed": lesson.id in completed,
                    "unlocked": services.lesson_is_unlocked(user, lesson),
                    "tests_count": lesson.tests.count(),
                }
            )
        skill_link = getattr(section, "skill_link", None)
        sections.append(
            {
                "obj": section,
                "lessons": lessons,
                "skill": skill_link.skill if skill_link else None,
                "complete": services.section_is_complete(user, section),
            }
        )
    return sections


@login_required
def course_detail(request, pk):
    """Карта курса: разделы-группы и уроки с прогрессом и замками."""
    course = get_object_or_404(Course, pk=pk)
    enrollment = Enrollment.objects.filter(user=request.user, course=course).first()
    sections = _course_structure(request.user, course)
    total_lessons = sum(len(s["lessons"]) for s in sections)
    percent = services.course_progress_percent(request.user, course) if total_lessons else 0
    context = {
        "course": course,
        "sections": sections,
        "enrollment": enrollment,
        "is_enrolled": enrollment is not None,
        "has_access": services.user_has_access(request.user, course),
        "percent": percent,
        "total_lessons": total_lessons,
        "next_lesson": services.next_lesson(request.user, course),
    }
    return render(request, "web/course_detail.html", context)


@login_required
def lesson_detail(request, pk):
    """Страница урока: материал, прогресс и тренажёр в конце."""
    lesson = get_object_or_404(Material, pk=pk)
    course = lesson.section.course
    if not Enrollment.objects.filter(user=request.user, course=course).exists():
        messages.info(request, "Сначала запишитесь на курс.")
        return redirect("web:course-detail", pk=course.id)
    if not services.lesson_is_unlocked(request.user, lesson):
        messages.warning(request, "Этот урок ещё закрыт — пройдите предыдущие.")
        return redirect("web:course-detail", pk=course.id)

    completed = MaterialProgress.objects.filter(user=request.user, material=lesson).exists()
    test = lesson.tests.first()
    context = {
        "lesson": lesson,
        "course": course,
        "section": lesson.section,
        "completed": completed,
        "test": test,
        "next_lesson": services.next_lesson(request.user, course),
    }
    return render(request, "web/lesson_detail.html", context)


@login_required
def trainer(request, pk):
    """RPG-тренажёр по уроку."""
    lesson = get_object_or_404(Material, pk=pk)
    course = lesson.section.course
    test = lesson.tests.first()
    if test is None:
        messages.info(request, "У этого урока нет тренажёра.")
        return redirect("web:lesson-detail", pk=lesson.id)
    if not services.lesson_is_unlocked(request.user, lesson):
        return redirect("web:course-detail", pk=course.id)
    questions = test.questions.prefetch_related("choices").order_by("order", "id")
    context = {"lesson": lesson, "course": course, "test": test, "questions": questions}
    return render(request, "web/trainer.html", context)


@login_required
@require_POST
def trainer_submit(request, pk):
    """Проверка ответов тренажёра + завершение урока при успехе."""
    lesson = get_object_or_404(Material, pk=pk)
    test = lesson.tests.first()
    if test is None:
        return redirect("web:lesson-detail", pk=lesson.id)

    answers = []
    for question in test.questions.all():
        if question.kind == question.Kind.TEXT:
            answers.append(
                {
                    "question": question.id,
                    "text": request.POST.get(f"q_{question.id}_text", ""),
                }
            )
        else:
            chosen = request.POST.getlist(f"q_{question.id}")
            answers.append(
                {"question": question.id, "choices": [int(c) for c in chosen if c.isdigit()]}
            )

    skills_before = set(_profile(request.user).skills.values_list("skill_id", flat=True))
    result = grade_test(request.user, test, answers)

    new_skills = []
    if result["is_passed"]:
        services.mark_material_complete(request.user, lesson)
        profile = _profile(request.user)
        new_skills = list(
            profile.skills.exclude(skill_id__in=skills_before).select_related("skill")
        )

    context = {
        "lesson": lesson,
        "course": lesson.section.course,
        "result": result,
        "new_skills": new_skills,
        "next_lesson": services.next_lesson(request.user, lesson.section.course),
    }
    return render(request, "web/trainer_result.html", context)


@login_required
def leaderboard(request):
    """Рейтинг игроков по опыту."""
    entries = list(services.leaderboard(limit=50))
    rows = [
        {"rank": i + 1, "username": p.user.username, "level": p.level, "xp": p.xp}
        for i, p in enumerate(entries)
    ]
    return render(request, "web/leaderboard.html", {"rows": rows})


@login_required
def profile_view(request):
    """Профиль игрока: «Мои скиллы», достижения и история начислений."""
    profile = _profile(request.user)
    earned_skills = profile.skills.select_related("skill", "course").all()
    all_skills = Skill.objects.all()
    earned_ids = set(profile.skills.values_list("skill_id", flat=True))
    enrollments = (
        Enrollment.objects.filter(user=request.user)
        .select_related("course")
        .order_by("-started_at")
    )
    context = {
        "profile": profile,
        "earned_skills": earned_skills,
        "all_skills": all_skills,
        "earned_skill_ids": earned_ids,
        "enrollments": enrollments,
        "achievements": Achievement.objects.all(),
        "earned_achievement_ids": set(
            PlayerAchievement.objects.filter(profile=profile).values_list(
                "achievement_id", flat=True
            )
        ),
        "transactions": profile.transactions.all()[:10],
    }
    return render(request, "web/profile.html", context)


@login_required
@require_POST
def complete_material(request, pk):
    """Отметить материал пройденным (HTMX-фрагмент или редирект)."""
    material = get_object_or_404(Material, pk=pk)
    _, created = services.mark_material_complete(request.user, material)
    if request.headers.get("HX-Request"):
        profile = _profile(request.user)
        return render(
            request,
            "web/partials/material_done.html",
            {"material": material, "profile": profile, "created": created},
        )
    return redirect("web:course-detail", pk=material.section.course_id)


@login_required
@require_POST
def enroll_course(request, pk):
    """Записаться на курс (платный требует покупки)."""
    course = get_object_or_404(Course, pk=pk)
    if not services.user_has_access(request.user, course):
        messages.warning(request, "Курс платный — сначала оформите покупку.")
        return redirect("web:course-detail", pk=course.id)
    _, created = services.enroll(request.user, course)
    if created:
        messages.success(request, f"Вы записались на курс «{course.title}»! +10 опыта")
    return redirect("web:course-detail", pk=course.id)


@login_required
@require_POST
def buy_course(request, pk):
    """Купить курс (mock-оплата) и получить доступ."""
    course = get_object_or_404(Course, pk=pk)
    if not course.is_paid:
        messages.info(request, "Этот курс бесплатный — можно сразу записаться.")
        return redirect("web:course-detail", pk=course.id)
    _, created = services.purchase_course(request.user, course)
    if created:
        messages.success(
            request,
            f"Курс «{course.title}» куплен за {course.price} ₽! Доступ открыт, +20 опыта.",
        )
    return redirect("web:course-detail", pk=course.id)
