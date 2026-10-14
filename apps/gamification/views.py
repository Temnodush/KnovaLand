from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.materials.models import Material

from . import services
from .models import Achievement, Enrollment
from .serializers import (
    AchievementSerializer,
    EnrollmentSerializer,
    EnrollRequestSerializer,
    LeaderboardEntrySerializer,
    MaterialProgressRequestSerializer,
    PlayerProfileSerializer,
)


class MyProfileView(generics.RetrieveAPIView):
    """GET /api/game/profile/ — игровой профиль текущего пользователя."""

    serializer_class = PlayerProfileSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return services.get_profile(self.request.user)


class LeaderboardView(generics.ListAPIView):
    """GET /api/game/leaderboard/ — топ игроков по опыту."""

    serializer_class = LeaderboardEntrySerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        course_id = self.request.query_params.get("course")
        course = None
        if course_id:
            from apps.courses.models import Course

            course = Course.objects.filter(id=course_id).first()
        entries = list(services.leaderboard(limit=50, course=course))
        for index, entry in enumerate(entries, start=1):
            entry.rank = index
        return entries


class AchievementListView(generics.ListAPIView):
    """GET /api/game/achievements/ — список достижений и статус получения."""

    serializer_class = AchievementSerializer
    permission_classes = [permissions.IsAuthenticated]
    queryset = Achievement.objects.all()
    pagination_class = None


class MyEnrollmentsView(generics.ListAPIView):
    """GET /api/game/enrollments/ — курсы текущего пользователя."""

    serializer_class = EnrollmentSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Enrollment.objects.filter(user=self.request.user).select_related("course")


class EnrollView(APIView):
    """POST /api/game/enroll/ — записаться на курс."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = EnrollRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment, created = services.enroll(request.user, serializer.validated_data["course"])
        return Response(
            {
                "enrollment": EnrollmentSerializer(enrollment).data,
                "created": created,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class CompleteMaterialView(APIView):
    """POST /api/game/progress/ — отметить материал пройденным."""

    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = MaterialProgressRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        material = Material.objects.filter(id=serializer.validated_data["material"]).first()
        if material is None:
            return Response({"detail": "Материал не найден."}, status=status.HTTP_404_NOT_FOUND)
        record, created = services.mark_material_complete(request.user, material)
        profile = services.get_profile(request.user)
        return Response(
            {
                "material": material.id,
                "created": created,
                "xp": profile.xp,
                "level": profile.level,
            },
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )
