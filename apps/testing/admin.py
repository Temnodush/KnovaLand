from django.contrib import admin

from .models import Choice, Question, SubmissionAnswer, Test, TestSubmission


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 2


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "test", "order")
    list_filter = ("test",)
    search_fields = ("text",)
    inlines = (ChoiceInline,)


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    show_change_link = True


@admin.register(Test)
class TestAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "material", "owner", "passing_score", "created_at")
    list_filter = ("owner", "material__section__course")
    search_fields = ("title", "description")
    inlines = (QuestionInline,)


class SubmissionAnswerInline(admin.TabularInline):
    model = SubmissionAnswer
    extra = 0
    readonly_fields = ("question", "is_correct")


@admin.register(TestSubmission)
class TestSubmissionAdmin(admin.ModelAdmin):
    list_display = ("id", "test", "user", "score", "total", "percentage", "is_passed", "created_at")
    list_filter = ("is_passed", "test")
    search_fields = ("user__email", "test__title")
    inlines = (SubmissionAnswerInline,)


@admin.register(Choice)
class ChoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "text", "question", "is_correct")
    list_filter = ("is_correct",)
    search_fields = ("text",)
