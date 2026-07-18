from ..domain.entities import Question as DomainQuestion
from ..infrastructure.django_repositories import build_engine_for_session
from ..models import GameSession, PlayerAnswer


class GetActiveQuestion:
    """Consulta de solo lectura: la pregunta activa de la sala (si hay) y si un jugador ya la respondio.

    Se usa para poner al dia a un jugador que se reconecta a media partida.
    """

    def execute(self, session_id: int, player_id: int | None = None) -> tuple[DomainQuestion, bool] | None:
        session = GameSession.objects.get(id=session_id)
        if session.status != GameSession.Status.IN_PROGRESS:
            return None

        question = build_engine_for_session(session).current_question()
        if question is None:
            return None

        already_answered = player_id is not None and PlayerAnswer.objects.filter(
            player_id=player_id, question_id=question.id,
        ).exists()
        return question, already_answered
