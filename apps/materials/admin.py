from django.contrib import admin

from apps.courses.models import Section
from apps.users.admin_mixins import TeacherScopedAdmin

from .models import Material


@admin.register(Material)
class MaterialAdmin(TeacherScopedAdmin):
    """Преподаватель управляет материалами только своих курсов."""

    owner_path = "owner"
    list_display = ("id", "title", "section", "owner", "order", "created_at")
    list_filter = ("section__course",)
    search_fields = ("title", "content")

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("owner",)
        return ()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "section" and not request.user.is_superuser:
            kwargs["queryset"] = Section.objects.filter(course__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
