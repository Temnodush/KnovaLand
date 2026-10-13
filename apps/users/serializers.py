from django.contrib.auth import get_user_model
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Профиль пользователя (чтение)."""

    role_display = serializers.CharField(source="get_role_display", read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "role_display",
            "avatar",
            "date_joined",
        )
        read_only_fields = ("id", "email", "role", "date_joined")


class RegisterSerializer(serializers.ModelSerializer):
    """Регистрация нового пользователя."""

    password = serializers.CharField(write_only=True, min_length=8, style={"input_type": "password"})
    password2 = serializers.CharField(write_only=True, style={"input_type": "password"})

    class Meta:
        model = User
        fields = ("id", "username", "email", "password", "password2", "role")
        extra_kwargs = {"role": {"required": False}}

    def validate_email(self, value):
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value.lower()

    def validate(self, attrs):
        if attrs.get("password") != attrs.get("password2"):
            raise serializers.ValidationError({"password2": "Пароли не совпадают."})
        # Студент/преподаватель при регистрации; админа назначает только админ.
        if attrs.get("role") == User.Role.ADMIN:
            raise serializers.ValidationError({"role": "Роль администратора нельзя выбрать при регистрации."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        return user


class UserAdminSerializer(serializers.ModelSerializer):
    """Управление пользователями (только администратор)."""

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "first_name",
            "last_name",
            "role",
            "is_active",
            "is_staff",
            "date_joined",
        )
        read_only_fields = ("id", "date_joined")
