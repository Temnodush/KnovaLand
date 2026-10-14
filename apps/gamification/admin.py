from django.contrib import admin

from .models import (
    Achievement,
    Enrollment,
    MaterialProgress,
    PlayerAchievement,
    PlayerProfile,
    PlayerSkill,
    Purchase,
    SectionSkill,
    Skill,
    XPTransaction,
)


class PlayerAchievementInline(admin.TabularInline):
    model = PlayerAchievement
    extra = 0
    readonly_fields = ("achievement", "earned_at")


class PlayerSkillInline(admin.TabularInline):
    model = PlayerSkill
    extra = 0
    readonly_fields = ("skill", "earned_at")


@admin.register(PlayerProfile)
class PlayerProfileAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "level", "xp", "streak_days", "last_activity_date")
    list_filter = ("level",)
    search_fields = ("user__email", "user__username")
    inlines = (PlayerAchievementInline, PlayerSkillInline)


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ("id", "icon", "title", "code", "order")
    search_fields = ("title", "code")


@admin.register(SectionSkill)
class SectionSkillAdmin(admin.ModelAdmin):
    list_display = ("id", "section", "skill")
    list_filter = ("skill",)


@admin.register(PlayerSkill)
class PlayerSkillAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "skill", "course", "earned_at")
    list_filter = ("skill",)
    search_fields = ("profile__user__email",)


@admin.register(Achievement)
class AchievementAdmin(admin.ModelAdmin):
    list_display = ("id", "icon", "title", "code", "xp_reward", "order")
    search_fields = ("title", "code")


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "xp", "started_at", "completed_at")
    list_filter = ("course",)
    search_fields = ("user__email", "course__title")


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "course", "amount", "created_at")
    list_filter = ("course",)
    search_fields = ("user__email", "course__title")


@admin.register(MaterialProgress)
class MaterialProgressAdmin(admin.ModelAdmin):
    list_display = ("id", "user", "material", "completed_at")
    search_fields = ("user__email", "material__title")


@admin.register(XPTransaction)
class XPTransactionAdmin(admin.ModelAdmin):
    list_display = ("id", "profile", "amount", "reason", "created_at")
    list_filter = ("reason",)
    search_fields = ("profile__user__email",)
