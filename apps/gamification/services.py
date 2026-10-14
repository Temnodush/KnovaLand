"""Игровая логика: опыт, уровни, достижения, серии занятий, навыки."""

from datetime import timedelta

from django.utils import timezone

from apps.testing.models import TestSubmission

from .models import (
    Achievement,
    Enrollment,
    MaterialProgress,
    PlayerAchievement,
    PlayerProfile,
    PlayerSkill,
    Purchase,
    SectionSkill,
    XPTransaction,
)

# Пороговое значение опыта на «шаг» уровня (глобальный профиль).
LEVEL_BASE = 100

# Опыт курса за один уровень (уровневая система внутри курса).
COURSE_XP_PER_LEVEL = 100
XP_PER_LESSON = 100
XP_PER_TRAINER_PASS = 50
XP_PER_SKILL = 75
XP_PER_PURCHASE = 20


def xp_required_for_level(level):
    """Суммарный опыт, необходимый для достижения уровня `level`.

    Уровень 1 — 0 XP, 2 — 100, 3 — 300, 4 — 600 …
    Формула: 100 * (1 + 2 + … + (level-1)) = 50 * level * (level - 1).
    """
    if level <= 1:
        return 0
    return LEVEL_BASE // 2 * level * (level - 1)


def level_for_xp(xp):
    """Обратная функция: уровень по текущему опыту."""
    level = 1
    while xp_required_for_level(level + 1) <= xp:
        level += 1
    return level


def course_level_for_xp(xp):
    """Уровень внутри курса: каждые COURSE_XP_PER_LEVEL опыта — новый уровень."""
    return xp // COURSE_XP_PER_LEVEL + 1


def get_profile(user):
    """Профиль игрока, создаётся при первом обращении."""
    profile, _ = PlayerProfile.objects.get_or_create(user=user)
    return profile


# --- Начисление опыта и серии -------------------------------------------------
def award_xp(profile, amount, reason=""):
    """Начислить опыт, пересчитать уровень, зафиксировать серию и достижения."""
    if amount <= 0:
        return profile
    profile.xp += amount
    profile.level = level_for_xp(profile.xp)
    _touch_streak(profile)
    profile.save()
    XPTransaction.objects.create(profile=profile, amount=amount, reason=reason)
    check_achievements(profile)
    profile.refresh_from_db()
    return profile


def _touch_streak(profile):
    """Обновить серию дней подряд. Без сохранения — сохранение делает вызывающий."""
    today = timezone.localdate()
    last = profile.last_activity_date
    if last == today:
        return
    if last == today - timedelta(days=1):
        profile.streak_days += 1
    else:
        profile.streak_days = 1
    profile.last_activity_date = today


# --- Достижения ---------------------------------------------------------------
# Условие для каждого кода достижения. Функция получает профиль, возвращает bool.
ACHIEVEMENT_RULES = {
    "first_enrollment": lambda p: Enrollment.objects.filter(user=p.user).exists(),
    "first_test": lambda p: TestSubmission.objects.filter(user=p.user).exists(),
    "perfect_test": lambda p: TestSubmission.objects.filter(user=p.user, percentage=100).exists(),
    "xp_100": lambda p: p.xp >= 100,
    "xp_500": lambda p: p.xp >= 500,
    "streak_7": lambda p: p.streak_days >= 7,
    "course_complete": lambda p: Enrollment.objects.filter(
        user=p.user, completed_at__isnull=False
    ).exists(),
}


def seed_achievements():
    """Создать/обновить справочник достижений."""
    catalog = [
        ("first_enrollment", "Первый шаг", "Записаться на первый курс", "🚀", 10, 1),
        ("first_test", "Первое испытание", "Пройти первый тест", "⚔️", 15, 2),
        ("perfect_test", "Без единой ошибки", "Пройти тест на 100%", "🎯", 25, 3),
        ("xp_100", "Сотня опыта", "Накопить 100 опыта", "💯", 0, 4),
        ("xp_500", "Пять сотен", "Накопить 500 опыта", "🏆", 0, 5),
        ("streak_7", "Неделя силы", "Заниматься 7 дней подряд", "🔥", 30, 6),
        ("course_complete", "Покоритель курса", "Завершить курс полностью", "👑", 50, 7),
    ]
    for code, title, desc, icon, reward, order in catalog:
        Achievement.objects.update_or_create(
            code=code,
            defaults={
                "title": title,
                "description": desc,
                "icon": icon,
                "xp_reward": reward,
                "order": order,
            },
        )


def check_achievements(profile):
    """Выдать профилю все достижения, условия которых выполнены."""
    earned_codes = set(profile.achievements.values_list("achievement__code", flat=True))
    newly_earned = []
    bonus = 0
    for achievement in Achievement.objects.all():
        if achievement.code in earned_codes:
            continue
        rule = ACHIEVEMENT_RULES.get(achievement.code)
        if rule and rule(profile):
            PlayerAchievement.objects.create(profile=profile, achievement=achievement)
            newly_earned.append(achievement)
            bonus += achievement.xp_reward

    if bonus:
        profile.xp += bonus
        profile.level = level_for_xp(profile.xp)
        profile.save(update_fields=["xp", "level", "updated_at"])
    return newly_earned


# --- Прогрессия ---------------------------------------------------------------
def lessons_of_course(course):
    """Упорядоченный список объектов уроков курса (по разделам и порядку)."""
    sections = list(course.sections.order_by("order", "id"))
    lessons = []
    for section in sections:
        lessons.extend(section.materials.order_by("order", "id"))
    return lessons


def completed_lesson_ids(user, course):
    return set(
        MaterialProgress.objects.filter(user=user, material__section__course=course).values_list(
            "material_id", flat=True
        )
    )


def lesson_is_unlocked(user, material):
    """Урок открыт, если он первый в курсе или предыдущий урок уже пройден."""
    course = material.section.course
    lessons = lessons_of_course(course)
    ids = [lesson.id for lesson in lessons]
    if material.id not in ids:
        return False
    index = ids.index(material.id)
    if index == 0:
        return True
    previous_id = ids[index - 1]
    return MaterialProgress.objects.filter(user=user, material_id=previous_id).exists()


def next_lesson(user, course):
    """Первый доступный (открытый и непройденный) урок курса."""
    done = completed_lesson_ids(user, course)
    for lesson in lessons_of_course(course):
        if lesson.id not in done and lesson_is_unlocked(user, lesson):
            return lesson
    return None


def award_course_xp(user, course, amount, reason=""):
    """Начислить опыт внутри курса (для уровневой системы курса)."""
    if amount <= 0:
        return None
    enrollment, _ = Enrollment.objects.get_or_create(user=user, course=course)
    enrollment.xp += amount
    enrollment.save(update_fields=["xp"])
    return enrollment


def section_is_complete(user, section):
    """Все ли уроки раздела пройдены."""
    lesson_ids = list(section.materials.values_list("id", flat=True))
    if not lesson_ids:
        return False
    done = MaterialProgress.objects.filter(user=user, material_id__in=lesson_ids).count()
    return done >= len(lesson_ids)


def check_skills(user, course=None):
    """Выдать навыки за полностью пройденные группы уроков. Возвращает новые навыки."""
    profile = get_profile(user)
    earned = set(profile.skills.values_list("skill_id", flat=True))
    newly = []
    links = SectionSkill.objects.select_related("skill", "section__course")
    for link in links:
        if link.skill_id in earned:
            continue
        if course is not None and link.section.course_id != course.id:
            continue
        if section_is_complete(user, link.section):
            PlayerSkill.objects.create(
                profile=profile, skill=link.skill, course=link.section.course
            )
            earned.add(link.skill_id)
            newly.append(link.skill)
    if newly:
        award_xp(profile, XP_PER_SKILL * len(newly), reason="skill")
    return newly


def mark_material_complete(user, material):
    """Отметить урок пройденным: глобальный и курсовой опыт, проверка навыков."""
    record, created = MaterialProgress.objects.get_or_create(user=user, material=material)
    if created:
        course = material.section.course
        award_xp(get_profile(user), 10, reason=f"lesson:{material.id}")
        award_course_xp(user, course, XP_PER_LESSON, reason=f"lesson:{material.id}")
        check_skills(user, course)
        refresh_course_completion(user, course)
    return record, created


def enroll(user, course):
    """Записать пользователя на курс."""
    enrollment, created = Enrollment.objects.get_or_create(user=user, course=course)
    if created:
        profile = get_profile(user)
        award_xp(profile, 10, reason=f"enroll:{course.id}")
    return enrollment, created


# --- Покупка курсов (монетизация) --------------------------------------------
def user_has_access(user, course):
    """Есть ли у пользователя доступ к курсу: бесплатный или купленный."""
    if not course.is_paid:
        return True
    return Purchase.objects.filter(user=user, course=course).exists()


def purchase_course(user, course):
    """Купить курс: записать покупку и сразу зачислить пользователя.

    Возвращает (purchase, created). Идемпотентно.
    """
    purchase, created = Purchase.objects.get_or_create(
        user=user, course=course, defaults={"amount": course.price}
    )
    if created:
        award_xp(get_profile(user), XP_PER_PURCHASE, reason=f"purchase:{course.id}")
        enroll(user, course)
    return purchase, created


def refresh_course_completion(user, course):
    """Если все материалы курса пройдены — отметить зачисление завершённым."""
    material_ids = list(
        course.sections.values_list("materials__id", flat=True).exclude(materials__id=None)
    )
    if not material_ids:
        return None
    done = MaterialProgress.objects.filter(user=user, material_id__in=material_ids).count()
    enrollment = Enrollment.objects.filter(user=user, course=course).first()
    if enrollment and enrollment.completed_at is None and done >= len(material_ids):
        enrollment.completed_at = timezone.now()
        enrollment.save(update_fields=["completed_at"])
        award_xp(get_profile(user), 50, reason=f"course_complete:{course.id}")
    return enrollment


def course_progress_percent(user, course):
    """Процент прохождения курса пользователем."""
    material_ids = list(
        course.sections.values_list("materials__id", flat=True).exclude(materials__id=None)
    )
    if not material_ids:
        return 0
    done = MaterialProgress.objects.filter(user=user, material_id__in=material_ids).count()
    return round(done / len(material_ids) * 100, 1)


def leaderboard(limit=50, course=None):
    """Топ игроков по опыту (можно ограничить одним курсом)."""
    qs = PlayerProfile.objects.select_related("user").order_by("-xp", "user__username")
    if course is not None:
        user_ids = Enrollment.objects.filter(course=course).values_list("user_id", flat=True)
        qs = qs.filter(user_id__in=user_ids)
    return qs[:limit]
