from rest_framework import viewsets

from apps.users.permissions import IsOwnerOrAdminOrReadOnly

from .models import Course, Section
from .serializers import CourseDetailSerializer, CourseSerializer, SectionSerializer


class CourseViewSet(viewsets.ModelViewSet):
    """CRUD курсов.

    - Админ: все курсы.
    - Преподаватель: видит все, изменяет только свои.
    - Студент: видит только опубликованные курсы, только чтение.
    """

    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filterset_fields = ("owner", "is_published")
    search_fields = ("title", "description")
    ordering_fields = ("created_at", "title")

    def get_queryset(self):
        user = self.request.user
        qs = Course.objects.select_related("owner").all()
        if not user.is_authenticated:
            return qs.none()
        if user.is_admin:
            return qs
        if user.is_teacher:
            return qs
        return qs.filter(is_published=True)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CourseDetailSerializer
        return CourseSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class SectionViewSet(viewsets.ModelViewSet):
    """CRUD разделов. Фильтр по курсу: ?course=<id>."""

    serializer_class = SectionSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filterset_fields = ("course",)
    search_fields = ("title", "description")
    ordering_fields = ("order", "created_at")

    def get_queryset(self):
        user = self.request.user
        qs = Section.objects.select_related("course", "course__owner").all()
        if not user.is_authenticated:
            return qs.none()
        if user.is_admin or user.is_teacher:
            return qs
        return qs.filter(course__is_published=True)
