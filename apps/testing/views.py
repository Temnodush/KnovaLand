from django.db import transaction
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from apps.users.permissions import IsOwnerOrAdminOrReadOnly, IsStudent

from .models import SubmissionAnswer, Test, TestSubmission
from .serializers import (
    SubmissionResultSerializer,
    SubmitSerializer,
    TestStudentSerializer,
    TestTeacherSerializer,
)


class TestViewSet(viewsets.ModelViewSet):
    """Тесты.

    - Преподаватель/админ: полный CRUD со всеми правильными ответами.
    - Студент: чтение без правильных ответов + прохождение (submit).
    """

    permission_classes = [IsOwnerOrAdminOrReadOnly]
    filterset_fields = ("material",)
    search_fields = ("title", "description")
    ordering_fields = ("created_at", "title")

    def get_queryset(self):
        user = self.request.user
        qs = Test.objects.select_related(
            "material", "material__section", "material__section__course"
        ).all()
        if not user.is_authenticated:
            return qs.none()
        if user.is_admin or user.is_teacher:
            return qs
        return qs.filter(material__section__course__is_published=True)

    def get_serializer_class(self):
        user = self.request.user
        if getattr(user, "is_authenticated", False) and getattr(user, "is_student", False):
            return TestStudentSerializer
        return TestTeacherSerializer

    def perform_create(self, serializer):
        material = serializer.validated_data["material"]
        serializer.save(owner=material.section.course.owner)

    @action(detail=True, methods=["post"], permission_classes=[IsStudent])
    def submit(self, request, pk=None):
        """POST /api/tests/{id}/submit/ — проверка ответов (отдельный запрос)."""
        test = self.get_object()
        payload = SubmitSerializer(data=request.data)
        payload.is_valid(raise_exception=True)

        answer_map = {
            item["question"]: set(item["choices"]) for item in payload.validated_data["answers"]
        }

        questions = list(test.questions.prefetch_related("choices"))
        score = 0
        details = []

        with transaction.atomic():
            submission = TestSubmission.objects.create(
                test=test, user=request.user, total=len(questions)
            )
            for question in questions:
                correct_ids = set(question.correct_choice_ids())
                selected_ids = answer_map.get(question.id, set())
                # Ответ верен, только если выбраны все правильные и нет лишних.
                is_correct = bool(correct_ids) and selected_ids == correct_ids
                if is_correct:
                    score += 1

                answer = SubmissionAnswer.objects.create(
                    submission=submission, question=question, is_correct=is_correct
                )
                # Оставляем только варианты, относящиеся к этому вопросу.
                valid_ids = {
                    cid
                    for cid in selected_ids
                    if cid in set(question.choices.values_list("id", flat=True))
                }
                answer.selected_choices.set(valid_ids)

                details.append(
                    {
                        "question": question.id,
                        "is_correct": is_correct,
                        "selected_choices": sorted(valid_ids),
                        "correct_choices": sorted(correct_ids),
                    }
                )

            total = len(questions)
            percentage = round(score / total * 100, 2) if total else 0.0
            submission.score = score
            submission.percentage = percentage
            submission.is_passed = percentage >= test.passing_score
            submission.save()

        return Response(
            {
                "submission_id": submission.id,
                "test": test.id,
                "score": score,
                "total": total,
                "percentage": percentage,
                "is_passed": submission.is_passed,
                "passing_score": test.passing_score,
                "details": details,
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["get"], url_path="results")
    def results(self, request, pk=None):
        """GET /api/tests/{id}/results/ — результаты теста (владелец/админ)."""
        test = self.get_object()
        if not (request.user.is_admin or test.owner == request.user):
            return Response(
                {"detail": "Недостаточно прав для просмотра результатов."},
                status=status.HTTP_403_FORBIDDEN,
            )
        submissions = test.submissions.select_related("user").order_by("-created_at")
        serializer = SubmissionResultSerializer(submissions, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"], url_path="my-results", permission_classes=[IsStudent])
    def my_results(self, request):
        """GET /api/tests/my-results/ — результаты текущего студента."""
        submissions = (
            TestSubmission.objects.filter(user=request.user)
            .select_related("test")
            .order_by("-created_at")
        )
        serializer = SubmissionResultSerializer(submissions, many=True)
        return Response(serializer.data)
