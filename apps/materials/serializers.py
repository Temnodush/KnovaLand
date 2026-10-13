from rest_framework import serializers

from .models import Material


class MaterialSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    section_title = serializers.CharField(source="section.title", read_only=True)
    tests_count = serializers.IntegerField(source="tests.count", read_only=True)

    class Meta:
        model = Material
        fields = (
            "id",
            "section",
            "section_title",
            "title",
            "content",
            "video_url",
            "order",
            "owner",
            "tests_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")

    def validate_section(self, section):
        request = self.context.get("request")
        if request and not request.user.is_admin and section.course.owner != request.user:
            raise serializers.ValidationError("Можно добавлять материалы только в свои курсы.")
        return section
