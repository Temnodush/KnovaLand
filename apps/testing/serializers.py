from django.db import transaction
from rest_framework import serializers

from .models import Choice, Question, SubmissionAnswer, Test, TestSubmission


# ---------------------------------------------------------------------------
# Студенческие сериализаторы (без правильных ответов!)
# ---------------------------------------------------------------------------
class ChoiceStudentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text")


class QuestionStudentSerializer(serializers.ModelSerializer):
    choices = ChoiceStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Question
        fields = ("id", "text", "kind", "order", "choices")


class TestStudentSerializer(serializers.ModelSerializer):
    questions = QuestionStudentSerializer(many=True, read_only=True)

    class Meta:
        model = Test
        fields = ("id", "material", "title", "description", "passing_score", "questions")


# ---------------------------------------------------------------------------
# Преподавательские сериализаторы (полный доступ + правильные ответы)
# ---------------------------------------------------------------------------
class ChoiceTeacherSerializer(serializers.ModelSerializer):
    class Meta:
        model = Choice
        fields = ("id", "text", "is_correct")


class QuestionTeacherSerializer(serializers.ModelSerializer):
    choices = ChoiceTeacherSerializer(many=True, required=False)

    class Meta:
        model = Question
        fields = ("id", "text", "kind", "answer_text", "order", "choices")

    def validate(self, attrs):
        kind = attrs.get("kind", getattr(self.instance, "kind", Question.Kind.CHOICE))
        if kind == Question.Kind.TEXT:
            answer_text = attrs.get("answer_text", getattr(self.instance, "answer_text", ""))
            if not (answer_text or "").strip():
                raise serializers.ValidationError(
                    {"answer_text": "Укажите правильный ответ для вопроса с ручным вводом."}
                )
        else:
            choices = attrs.get("choices")
            if choices is not None:
                if not choices:
                    raise serializers.ValidationError(
                        {"choices": "У вопроса должен быть хотя бы один вариант ответа."}
                    )
                if not any(c.get("is_correct") for c in choices):
                    raise serializers.ValidationError(
                        {"choices": "Отметьте хотя бы один правильный вариант ответа."}
                    )
        return attrs


class TestTeacherSerializer(serializers.ModelSerializer):
    questions = QuestionTeacherSerializer(many=True)
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Test
        fields = (
            "id",
            "material",
            "title",
            "description",
            "passing_score",
            "owner",
            "questions",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "owner", "created_at", "updated_at")

    def validate_material(self, material):
        request = self.context.get("request")
        if request and not request.user.is_admin and material.section.course.owner != request.user:
            raise serializers.ValidationError("Можно создавать тесты только в своих материалах.")
        return material

    @transaction.atomic
    def create(self, validated_data):
        questions_data = validated_data.pop("questions", [])
        test = Test.objects.create(**validated_data)
        self._sync_questions(test, questions_data)
        return test

    @transaction.atomic
    def update(self, instance, validated_data):
        questions_data = validated_data.pop("questions", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        if questions_data is not None:
            instance.questions.all().delete()
            self._sync_questions(instance, questions_data)
        return instance

    @staticmethod
    def _sync_questions(test, questions_data):
        for q_data in questions_data:
            choices_data = q_data.pop("choices", [])
            question = Question.objects.create(test=test, **q_data)
            for c_data in choices_data:
                Choice.objects.create(question=question, **c_data)


# ---------------------------------------------------------------------------
# Прохождение теста
# ---------------------------------------------------------------------------
class SubmitAnswerSerializer(serializers.Serializer):
    question = serializers.IntegerField()
    choices = serializers.ListField(
        child=serializers.IntegerField(), allow_empty=True, required=False, default=list
    )
    text = serializers.CharField(required=False, allow_blank=True, default="")


class SubmitSerializer(serializers.Serializer):
    answers = SubmitAnswerSerializer(many=True)

    def validate_answers(self, value):
        if not value:
            raise serializers.ValidationError("Нужно передать хотя бы один ответ.")
        return value


class SubmissionResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestSubmission
        fields = ("id", "test", "user", "score", "total", "percentage", "is_passed", "created_at")


class SubmissionAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source="question.text", read_only=True)

    class Meta:
        model = SubmissionAnswer
        fields = (
            "id",
            "question",
            "question_text",
            "selected_choices",
            "text_answer",
            "is_correct",
        )
