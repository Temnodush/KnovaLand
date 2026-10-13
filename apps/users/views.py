from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status, viewsets
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .permissions import IsAdmin
from .serializers import (
    RegisterSerializer,
    UserAdminSerializer,
    UserSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register/ — регистрация пользователя."""

    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [permissions.AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)


class MeView(generics.RetrieveUpdateAPIView):
    """GET/PATCH /api/users/me/ — профиль текущего пользователя."""

    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user


class UserViewSet(viewsets.ModelViewSet):
    """CRUD пользователей. Доступ только администратору."""

    queryset = User.objects.all().order_by("id")
    serializer_class = UserAdminSerializer
    permission_classes = [IsAdmin]
    search_fields = ("email", "username", "first_name", "last_name")
    filterset_fields = ("role", "is_active")


# JWT endpoints
class LoginView(TokenObtainPairView):
    """POST /api/auth/token/ — вход, выдача access/refresh."""


class RefreshView(TokenRefreshView):
    """POST /api/auth/token/refresh/ — обновление access-токена."""
