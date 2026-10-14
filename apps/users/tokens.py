"""Подписанные токены для подтверждения email (без хранения в БД)."""

from django.core.signing import BadSignature, SignatureExpired, TimestampSigner

_VERIFY_SALT = "users.email-verify"
_signer = TimestampSigner(salt=_VERIFY_SALT)

# Ссылка подтверждения живёт 3 дня.
DEFAULT_MAX_AGE = 60 * 60 * 24 * 3


def make_email_verification_token(user):
    """Создать подписанный токен подтверждения для пользователя."""
    return _signer.sign(str(user.pk))


def read_email_verification_token(token, max_age=DEFAULT_MAX_AGE):
    """Проверить токен. Вернуть pk пользователя или None, если токен неверен/просрочен."""
    try:
        value = _signer.unsign(token, max_age=max_age)
    except (BadSignature, SignatureExpired):
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None
