from ..domain.lifecycle import SessionLifecycleService, SessionStatus
from ..models import GameSession


class EndSession:
    """Termina una partida en curso (el host la corta antes de agotar las preguntas)."""

    def execute(self, session_id: int) -> GameSession:
        session = GameSession.objects.get(id=session_id)
        lifecycle = SessionLifecycleService()
        new_status = lifecycle.transition(SessionStatus(session.status), SessionStatus.FINISHED)

        session.status = new_status.value
        session.save(update_fields=['status'])
        return session
