from rest_framework import serializers

from .models import Course, Section


class SectionSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Section
        fields = ("id", "course", "course_title", "title", "description", "order", "created_at")
        read_only_fields = ("id", "created_at")

    def validate_course(self, course):
        request = self.context.get("request")
        if request and not request.user.is_admin and course.owner != request.user:
            raise serializers.ValidationError("Можно добавлять разделы только в свои курсы.")
        return course


class CourseSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    owner_email = serializers.CharField(source="owner.email", read_only=True)
    sections_count = serializers.IntegerField(source="sections.count", read_only=True)

    class Meta:
        model = Course
        fields = (
            "id",
            "title",
            "description",
            "owner",
            "owner_email",
            "is_published",
            "sections_count",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at")


class CourseDetailSerializer(CourseSerializer):
    sections = SectionSerializer(many=True, read_only=True)

    class Meta(CourseSerializer.Meta):
        fields = CourseSerializer.Meta.fields + ("sections",)
