"""Пользовательские фильтры шаблонов."""

import markdown as md
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter(name="markdownify")
def markdownify(text):
    """Преобразовать Markdown в HTML (для материалов уроков)."""
    if not text:
        return ""
    html = md.markdown(
        text,
        extensions=["fenced_code", "codehilite", "tables", "nl2br"],
    )
    return mark_safe(html)  # noqa: S308 — контент уроков создаётся преподавателем
