from rest_framework import serializers

from apps.courses.models import Course

from .models import Achievement, Enrollment, PlayerAchievement, PlayerProfile


class AchievementSerializer(serializers.ModelSerializer):
    earned = serializers.SerializerMethodField()

    class Meta:
        model = Achievement
        fields = ("id", "code", "title", "description", "icon", "xp_reward", "earned")

    def get_earned(self, achievement):
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return False
        profile = getattr(request.user, "player_profile", None)
        if profile is None:
            return False
        return profile.achievements.filter(achievement=achievement).exists()


class PlayerProfileSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    achievements = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()

    class Meta:
        model = PlayerProfile
        fields = (
            "username",
            "xp",
            "level",
            "xp_in_level",
            "xp_to_next_level",
            "level_progress_percent",
            "streak_days",
            "character",
            "achievements",
            "skills",
        )

    def get_achievements(self, profile):
        earned = PlayerAchievement.objects.filter(profile=profile).select_related("achievement")
        return [
            {
                "code": pa.achievement.code,
                "title": pa.achievement.title,
                "icon": pa.achievement.icon,
                "earned_at": pa.earned_at,
            }
            for pa in earned
        ]

    def get_skills(self, profile):
        earned = profile.skills.select_related("skill")
        return [
            {
                "code": ps.skill.code,
                "title": ps.skill.title,
                "icon": ps.skill.icon,
                "earned_at": ps.earned_at,
            }
            for ps in earned
        ]


class LeaderboardEntrySerializer(serializers.ModelSerializer):
    username = serializers.CharField(source="user.username", read_only=True)
    rank = serializers.IntegerField(read_only=True)

    class Meta:
        model = PlayerProfile
        fields = ("rank", "username", "level", "xp")


class EnrollmentSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Enrollment
        fields = (
            "id",
            "course",
            "course_title",
            "xp",
            "course_level",
            "started_at",
            "completed_at",
            "is_completed",
        )
        read_only_fields = (
            "id",
            "xp",
            "course_level",
            "started_at",
            "completed_at",
            "is_completed",
        )


class EnrollRequestSerializer(serializers.Serializer):
    course = serializers.PrimaryKeyRelatedField(queryset=Course.objects.all())


class MaterialProgressRequestSerializer(serializers.Serializer):
    material = serializers.IntegerField()
