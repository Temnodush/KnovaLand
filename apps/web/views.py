"""Серверные (не-API) представления для геймифицированного веб-интерфейса."""
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_POST

from apps.courses.models import Course
from apps.gamification import services
from apps.gamification.models import Achievement, Enrollment, MaterialProgress, PlayerAchievement
from apps.materials.models import Material


def _profile(user):
    return services.get_profile(user)


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
                "percent": services.course_progress_percent(request.user, enrollment.course),
                "completed": enrollment.is_completed,
            }
        )

    earned_ids = set(
        PlayerAchievement.objects.filter(profile=profile).values_list("achievement_id", flat=True)
    )
    achievements = Achievement.objects.all()

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
        "available_courses": available,
    }
    return render(request, "web/dashboard.html", context)


@login_required
def course_detail(request, pk):
    """Карта курса: разделы и материалы с прогрессом."""
    course = get_object_or_404(Course, pk=pk)
    is_enrolled = Enrollment.objects.filter(user=request.user, course=course).exists()
    completed_ids = set(
        MaterialProgress.objects.filter(
            user=request.user, material__section__course=course
        ).values_list("material_id", flat=True)
    )
    sections = []
    total_materials = 0
    for section in course.sections.prefetch_related("materials").all():
        materials = []
        for material in section.materials.all():
            total_materials += 1
            materials.append(
                {
                    "obj": material,
                    "completed": material.id in completed_ids,
                    "tests_count": material.tests.count(),
                }
            )
        sections.append({"obj": section, "materials": materials})

    percent = services.course_progress_percent(request.user, course) if total_materials else 0
    context = {
        "course": course,
        "sections": sections,
        "is_enrolled": is_enrolled,
        "percent": percent,
        "total_materials": total_materials,
    }
    return render(request, "web/course_detail.html", context)


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
    """Профиль игрока: достижения и последние начисления."""
    profile = _profile(request.user)
    earned = PlayerAchievement.objects.filter(profile=profile).select_related("achievement")
    context = {
        "profile": profile,
        "earned": earned,
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
    """Записаться на курс."""
    course = get_object_or_404(Course, pk=pk)
    _, created = services.enroll(request.user, course)
    if created:
        messages.success(request, f"Вы записались на курс «{course.title}»! +10 опыта")
    return redirect("web:course-detail", pk=course.id)
