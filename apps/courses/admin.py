from django.contrib import admin

from .models import Course, Section


class SectionInline(admin.TabularInline):
    model = Section
    extra = 1


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ("id", "icon", "title", "owner", "price", "is_published", "created_at")
    list_filter = ("is_published", "owner")
    search_fields = ("title", "description")
    inlines = (SectionInline,)


@admin.register(Section)
class SectionAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "course", "order")
    list_filter = ("course",)
    search_fields = ("title",)
