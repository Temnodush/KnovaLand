from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from .models import User


@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = ("id", "email", "username", "role", "is_active", "is_staff")
    list_filter = ("role", "is_active", "is_staff", "is_superuser")
    search_fields = ("email", "username", "first_name", "last_name")
    ordering = ("id",)
    fieldsets = DjangoUserAdmin.fieldsets + (("Роли и профиль", {"fields": ("role", "avatar")}),)
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (("Роли и профиль", {"fields": ("role", "email")}),)
