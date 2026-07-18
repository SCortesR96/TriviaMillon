from django.db.models import F

from apps.questions.models import Question as ORMQuestion

from ..domain.entities import AnswerOption as DomainAnswerOption
from ..domain.entities import Question as DomainQuestion
from ..domain.engine import GameEngine
from ..domain.ladder import FixedLadderStrategy, LadderLevel
from ..domain.lifecycle import SessionStatus
from ..models import GameSession, Player, PrizeLevel


class DjangoQuestionRepository:
    """Implementacion de QuestionRepository sobre el ORM de Django."""

    def get_questions_for_set(self, question_set_id: int) -> list[DomainQuestion]:
        questions = ORMQuestion.objects.filter(question_set_id=question_set_id).prefetch_related('options')
        return [
            DomainQuestion(
                id=q.id,
                text=q.text,
                order=q.order,
                options=[
                    DomainAnswerOption(id=o.id, text=o.text, is_correct=o.is_correct)
                    for o in q.options.all()
                ],
            )
            for q in questions
        ]


class DjangoSessionRepository:
    """Implementacion de SessionRepository sobre el ORM de Django."""

    def get_status(self, session_id: int) -> SessionStatus:
        status = GameSession.objects.values_list('status', flat=True).get(id=session_id)
        return SessionStatus(status)

    def save_status(self, session_id: int, status: SessionStatus) -> None:
        GameSession.objects.filter(id=session_id).update(status=status.value)

    def get_current_level_index(self, session_id: int) -> int:
        return GameSession.objects.values_list('current_level_index', flat=True).get(id=session_id)

    def save_current_level_index(self, session_id: int, level_index: int) -> None:
        GameSession.objects.filter(id=session_id).update(current_level_index=level_index)


class DjangoPlayerRepository:
    """Implementacion de PlayerRepository sobre el ORM de Django."""

    def add_points(self, player_id: int, points: int) -> None:
        Player.objects.filter(id=player_id).update(score=F('score') + points)

    def get_score(self, player_id: int) -> int:
        return Player.objects.values_list('score', flat=True).get(id=player_id)


def build_ladder_strategy(ladder_template_id: int) -> FixedLadderStrategy:
    levels = PrizeLevel.objects.filter(ladder_template_id=ladder_template_id)
    return FixedLadderStrategy([
        LadderLevel(index=level.index, points=level.points, is_checkpoint=level.is_checkpoint)
        for level in levels
    ])


def build_engine_for_session(session: GameSession) -> GameEngine:
    """Reconstruye el GameEngine de dominio a partir del estado persistido de una GameSession."""
    questions = DjangoQuestionRepository().get_questions_for_set(session.question_set_id)
    ladder = build_ladder_strategy(session.ladder_template_id)
    engine = GameEngine(questions, ladder)
    engine.status = SessionStatus(session.status)
    engine.current_level_index = session.current_level_index
    return engine
