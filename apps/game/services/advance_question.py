from ..domain.entities import Question as DomainQuestion
from ..infrastructure.django_repositories import build_engine_for_session
from ..models import GameSession


class AdvanceQuestion:
    """Avanza la partida a la siguiente pregunta, o la termina si ya no quedan preguntas."""

    def execute(self, session_id: int) -> DomainQuestion | None:
        session = GameSession.objects.get(id=session_id)
        engine = build_engine_for_session(session)

        next_question = engine.advance()

        session.status = engine.status.value
        session.current_level_index = engine.current_level_index
        session.save(update_fields=['status', 'current_level_index'])
        return next_question
