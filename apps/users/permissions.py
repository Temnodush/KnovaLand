from rest_framework.permissions import SAFE_METHODS, BasePermission


class IsAdmin(BasePermission):
    """Только администратор платформы."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_admin)


class IsTeacherOrAdmin(BasePermission):
    """Преподаватель или администратор (создание контента)."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and (user.is_teacher or user.is_admin))


class IsOwnerOrAdmin(BasePermission):
    """Изменять объект может его владелец или администратор.

    Предполагается, что у объекта есть поле/атрибут ``owner``.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_admin:
            return True
        owner = getattr(obj, "owner", None)
        return owner is not None and owner == user


class IsOwnerOrAdminOrReadOnly(BasePermission):
    """Чтение — всем авторизованным, запись — владельцу/админу/учителю.

    Для list/create (без объекта) запись разрешена учителю и админу.
    """

    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return user.is_teacher or user.is_admin

    def has_object_permission(self, request, view, obj):
        user = request.user
        if request.method in SAFE_METHODS:
            return True
        if user.is_admin:
            return True
        return getattr(obj, "owner", None) == user


class IsStudent(BasePermission):
    """Только студент."""

    def has_permission(self, request, view):
        user = request.user
        return bool(user and user.is_authenticated and user.is_student)
