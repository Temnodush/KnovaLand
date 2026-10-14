"""Миксины для админки: изоляция контента по владельцу-преподавателю."""

from django.contrib import admin


class TeacherScopedAdmin(admin.ModelAdmin):
    """Админка, ограниченная владельцем.

    - Суперпользователь видит и меняет всё.
    - Преподаватель (is_teacher) — только свои объекты.
    - Остальные — ничего.

    ``owner_path`` — путь к владельцу в ORM-фильтре: например ``owner``,
    ``course__owner`` или ``test__owner``.
    """

    owner_path = "owner"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if request.user.is_superuser:
            return qs
        if request.user.is_teacher:
            return qs.filter(**{self.owner_path: request.user})
        return qs.none()

    def has_module_permission(self, request):
        return request.user.is_superuser or request.user.is_teacher

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_teacher

    def has_add_permission(self, request):
        return request.user.is_superuser or request.user.is_teacher

    def has_change_permission(self, request, obj=None):
        # Объект всегда берётся из уже отфильтрованного get_queryset,
        # поэтому чужой объект сюда не попадёт.
        return request.user.is_superuser or request.user.is_teacher

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser or request.user.is_teacher


class SuperuserOnlyAdmin(admin.ModelAdmin):
    """Админка, доступная только суперпользователю."""

    def has_module_permission(self, request):
        return request.user.is_superuser

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_add_permission(self, request):
        return request.user.is_superuser

    def has_change_permission(self, request, obj=None):
        return request.user.is_superuser

    def has_delete_permission(self, request, obj=None):
        return request.user.is_superuser
