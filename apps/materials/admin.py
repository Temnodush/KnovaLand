from django.contrib import admin

from .models import Material


@admin.register(Material)
class MaterialAdmin(admin.ModelAdmin):
    list_display = ("id", "title", "section", "owner", "order", "created_at")
    list_filter = ("section__course", "owner")
    search_fields = ("title", "content")
