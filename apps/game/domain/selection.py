from .entities import Question


class QuestionSelectionService:
    """Unica responsabilidad: decidir cual es la pregunta de cada nivel de la partida."""

    def __init__(self, questions: list[Question]):
        self._questions = sorted(
            questions,
            key=lambda q: (q.order if q.order is not None else 0, q.id),
        )

    def total_questions(self) -> int:
        return len(self._questions)

    def question_at(self, level_index: int) -> Question | None:
        if 0 <= level_index < len(self._questions):
            return self._questions[level_index]
        return None
