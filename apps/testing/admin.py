from django.contrib import admin

from apps.materials.models import Material
from apps.users.admin_mixins import TeacherScopedAdmin

from .models import Choice, Question, SubmissionAnswer, Test, TestSubmission


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(TeacherScopedAdmin):
    owner_path = "test__owner"
    list_display = ("id", "text", "kind", "test", "order")
    list_filter = ("kind",)
    search_fields = ("text", "answer_text")
    inlines = (ChoiceInline,)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "test" and not request.user.is_superuser:
            kwargs["queryset"] = Test.objects.filter(owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Test)
class TestAdmin(TeacherScopedAdmin):
    """Владелец материала управляет тестами для него."""

    owner_path = "owner"
    list_display = ("id", "title", "material", "owner", "passing_score", "created_at")
    list_filter = ("material__section__course",)
    search_fields = ("title", "description")
    inlines = (QuestionInline,)

    def get_readonly_fields(self, request, obj=None):
        if not request.user.is_superuser:
            return ("owner",)
        return ()

    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            obj.owner = request.user
        super().save_model(request, obj, form, change)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "material" and not request.user.is_superuser:
            kwargs["queryset"] = Material.objects.filter(section__course__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


class SubmissionAnswerInline(admin.TabularInline):
    model = SubmissionAnswer
    extra = 0
    readonly_fields = ("question", "is_correct")


@admin.register(TestSubmission)
class TestSubmissionAdmin(TeacherScopedAdmin):
    owner_path = "test__owner"
    list_display = ("id", "test", "user", "score", "total", "percentage", "is_passed", "created_at")
    list_filter = ("is_passed",)
    search_fields = ("user__email", "test__title")
    inlines = (SubmissionAnswerInline,)

    def has_add_permission(self, request):
        return False


@admin.register(Choice)
class ChoiceAdmin(TeacherScopedAdmin):
    owner_path = "question__test__owner"
    list_display = ("id", "text", "question", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text",)

    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "question" and not request.user.is_superuser:
            kwargs["queryset"] = Question.objects.filter(test__owner=request.user)
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
