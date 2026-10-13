from rest_framework import viewsets

from apps.users.permissions import IsOwnerOrAdminOrReadOnly

from .models import Material
from .serializers import MaterialSerializer


class MaterialViewSet(viewsets.ModelViewSet):
    """CRUD материалов. Фильтр по разделу: ?section=<id>."""

    serializer_class = MaterialSerializer
    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filterset_fields = ("section",)
    search_fields = ("title", "content")
    ordering_fields = ("order", "created_at")

    def get_queryset(self):
        user = self.request.user
        qs = Material.objects.select_related("section", "section__course", "owner").all()
        if not user.is_authenticated:
            return qs.none()
        if user.is_admin or user.is_teacher:
            return qs
        return qs.filter(section__course__is_published=True)

    def perform_create(self, serializer):
        section = serializer.validated_data["section"]
        serializer.save(owner=section.course.owner)
