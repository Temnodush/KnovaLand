"""Отправка письма с подтверждением регистрации."""

import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from .tokens import make_email_verification_token

logger = logging.getLogger(__name__)


def build_verification_url(request, user):
    """Построить абсолютный URL подтверждения email."""
    token = make_email_verification_token(user)
    path = reverse("web:verify-email", kwargs={"token": token})
    return request.build_absolute_uri(path)


def send_verification_email(request, user):
    """Отправить письмо с ссылкой подтверждения. Возвращает URL (для отладки)."""
    site_name = getattr(settings, "SITE_NAME", "KnovaLand")
    url = build_verification_url(request, user)
    context = {"user": user, "url": url, "site_name": site_name}
    subject = f"{site_name}: подтверждение регистрации"
    text_body = render_to_string("registration/email_verify.txt", context)
    html_body = render_to_string("registration/email_verify.html", context)

    message = EmailMultiAlternatives(
        subject=subject,
        body=text_body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        to=[user.email],
    )
    message.attach_alternative(html_body, "text/html")
    message.send(fail_silently=False)
    return url


def try_send_verification_email(request, user):
    """Отправить письмо, не роняя запрос при ошибке SMTP. Возвращает True/False."""
    try:
        send_verification_email(request, user)
        return True
    except Exception:  # noqa: BLE001 — намеренно ловим любую ошибку отправки
        logger.exception("Не удалось отправить письмо подтверждения для %s", user.email)
        return False
