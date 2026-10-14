from django.conf import settings


def site(request):
    """Добавляет название сайта и игровой профиль в контекст шаблонов."""
    context = {"SITE_NAME": getattr(settings, "SITE_NAME", "Платформа")}
    user = getattr(request, "user", None)
    if user is not None and user.is_authenticated:
        from apps.gamification import services

        context["nav_profile"] = services.get_profile(user)
    return context
