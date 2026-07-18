from ..domain.entities import Question as DomainQuestion
from ..infrastructure.django_repositories import build_engine_for_session
from ..models import GameSession


class SessionNotInLobby(Exception):
    pass


class StartQuestion:
    """Arranca la partida: pasa de lobby a en_curso y deja lista la primera pregunta."""

    def execute(self, session_id: int) -> DomainQuestion | None:
        session = GameSession.objects.get(id=session_id)
        if session.status != GameSession.Status.LOBBY:
            raise SessionNotInLobby('La sala no esta en lobby, no se puede iniciar')

        engine = build_engine_for_session(session)
        engine.start()

        session.status = engine.status.value
        session.current_level_index = engine.current_level_index
        session.save(update_fields=['status', 'current_level_index'])
        return engine.current_question()
