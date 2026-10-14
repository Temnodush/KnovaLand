"""Миксины для админки: изоляция контента по владельцу-преподавателю."""

from django.contrib import admin


def _is_teacher(user):
    """Безопасно проверить роль: у AnonymousUser нет свойства is_teacher."""
    return bool(getattr(user, "is_teacher", False))


def _is_superuser(user):
    return bool(getattr(user, "is_superuser", False))


class TeacherScopedAdmin(admin.ModelAdmin):
    """Админка, ограниченная владельцем.

    - Суперпользователь видит и меняет всё.
    - Преподаватель (is_teacher) — только свои объекты.
    - Остальные (в т.ч. анонимные) — ничего.

    ``owner_path`` — путь к владельцу в ORM-фильтре: например ``owner``,
    ``course__owner`` или ``test__owner``.
    """

    owner_path = "owner"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if _is_superuser(request.user):
            return qs
        if _is_teacher(request.user):
            return qs.filter(**{self.owner_path: request.user})
        return qs.none()

    def has_module_permission(self, request):
        return _is_superuser(request.user) or _is_teacher(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_superuser(request.user) or _is_teacher(request.user)

    def has_add_permission(self, request):
        return _is_superuser(request.user) or _is_teacher(request.user)

    def has_change_permission(self, request, obj=None):
        # Объект всегда берётся из уже отфильтрованного get_queryset,
        # поэтому чужой объект сюда не попадёт.
        return _is_superuser(request.user) or _is_teacher(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_superuser(request.user) or _is_teacher(request.user)


class SuperuserOnlyAdmin(admin.ModelAdmin):
    """Админка, доступная только суперпользователю."""

    def has_module_permission(self, request):
        return _is_superuser(request.user)

    def has_view_permission(self, request, obj=None):
        return _is_superuser(request.user)

    def has_add_permission(self, request):
        return _is_superuser(request.user)

    def has_change_permission(self, request, obj=None):
        return _is_superuser(request.user)

    def has_delete_permission(self, request, obj=None):
        return _is_superuser(request.user)
