from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend
from django.db.models import Q


class EmailOrUsernameBackend(ModelBackend):
    """Позволяет аутентификацию по email ИЛИ по username.

    В проекте USERNAME_FIELD = 'email', поэтому стандартный бэкенд принимает только
    email. Этот бэкенд делает вход удобным: подходит и логин, и почта.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        User = get_user_model()
        if username is None:
            username = kwargs.get(User.USERNAME_FIELD)
        if username is None or password is None:
            return None
        try:
            user = User.objects.get(Q(username__iexact=username) | Q(email__iexact=username))
        except User.DoesNotExist:
            # Защита от тайминг-атак: прогоняем хэш пароля вхолостую.
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            user = (
                User.objects.filter(Q(username__iexact=username) | Q(email__iexact=username))
                .order_by("id")
                .first()
            )
        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
