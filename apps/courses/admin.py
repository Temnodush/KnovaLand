from django.contrib import admin

from apps.users.admin_mixins import TeacherScopedAdmin

from .models import Course, Section


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


@admin.register(Course)
class CourseAdmin(TeacherScopedAdmin):
    """Преподаватель управляет только своими курсами."""

    owner_path = "owner"
    list_display = ("id", "icon", "title", "owner", "price", "is_published", "created_at")
    list_filter = ("is_published",)
    search_fields = ("title", "description")
    inlines = (SectionInline,)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("owner",)
        return ()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.owner = request.user
        super().save_model(request, obj, form, change)


@admin.register(Section)
class SectionAdmin(TeacherScopedAdmin):
    owner_path = "course__owner"
    list_display = ("id", "title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "course" and not request.user.is_superuser:
            kwargs["queryset"] = Course.objects.filter(owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
