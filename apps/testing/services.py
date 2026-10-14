"""Проверка ответов на тест (общая логика для API и веб-тренажёра)."""

from django.db import transaction

from .models import SubmissionAnswer, TestSubmission


def grade_test(user, test, answers):
    """Проверить ответы и сохранить результат.

    ``answers`` — список словарей вида ``{"question": <id>, "choices": [<id>, ...]}``.

    Возвращает dict: submission, score, total, percentage, is_passed, passing_score, details.
    """
    answer_map = {item["question"]: set(item.get("choices") or []) for item in answers}
    text_map = {item["question"]: (item.get("text") or "") for item in answers}
    questions = list(test.questions.prefetch_related("choices"))

    # Сначала считаем результат, чтобы создать запись с финальными значениями:
    # сигналы награждают опыт именно при создании TestSubmission (created=True).
    computed = []
    score = 0
    for question in questions:
        valid_choice_ids = set(question.choices.values_list("id", flat=True))
        selected_ids = answer_map.get(question.id, set())
        typed_text = text_map.get(question.id, "")

        if question.kind == question.Kind.TEXT:
            is_correct = bool(question.correct_text_answers()) and question.check_text(typed_text)
            valid_selected = set()
        else:
            correct_ids = set(question.correct_choice_ids())
            # Ответ верен, только если выбраны все правильные и нет лишних.
            is_correct = bool(correct_ids) and selected_ids == correct_ids
            valid_selected = {cid for cid in selected_ids if cid in valid_choice_ids}

        if is_correct:
            score += 1
        computed.append((question, is_correct, valid_selected, typed_text))

    total = len(questions)
    percentage = round(score / total * 100, 2) if total else 0.0
    is_passed = percentage >= test.passing_score

    details = []
    with transaction.atomic():
        submission = TestSubmission.objects.create(
            test=test,
            user=user,
            score=score,
            total=total,
            percentage=percentage,
            is_passed=is_passed,
        )
        for question, is_correct, valid_selected, typed_text in computed:
            answer = SubmissionAnswer.objects.create(
                submission=submission,
                question=question,
                text_answer=typed_text,
                is_correct=is_correct,
            )
            answer.selected_choices.set(valid_selected)
            details.append(
                {
                    "question": question.id,
                    "is_correct": is_correct,
                    "selected_choices": sorted(valid_selected),
                    "text_answer": typed_text,
                    "correct_choices": sorted(set(question.correct_choice_ids())),
                    "correct_text": (
                        question.answer_text if question.kind == question.Kind.TEXT else ""
                    ),
                }
            )

    return {
        "submission": submission,
        "submission_id": submission.id,
        "test": test.id,
        "score": score,
        "total": total,
        "percentage": percentage,
        "is_passed": is_passed,
        "passing_score": test.passing_score,
        "details": details,
    }
