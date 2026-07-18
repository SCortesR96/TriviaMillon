from ..models import GameSession


class SessionNotInProgress(Exception):
    pass


class PauseSession:
    """Pausa una partida en curso: mientras esta pausada no se aceptan respuestas."""

    def execute(self, session_id: int) -> GameSession:
        session = GameSession.objects.get(id=session_id)
        if session.status != GameSession.Status.IN_PROGRESS:
            raise SessionNotInProgress('Solo se puede pausar una partida en curso')
        session.is_paused = True
        session.save(update_fields=['is_paused'])
        return session


class ResumeSession:
    """Reanuda una partida pausada."""

    def execute(self, session_id: int) -> GameSession:
        session = GameSession.objects.get(id=session_id)
        session.is_paused = False
        session.save(update_fields=['is_paused'])
        return session
