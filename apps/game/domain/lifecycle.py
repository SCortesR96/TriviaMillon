from enum import Enum


class SessionStatus(Enum):
    LOBBY = 'lobby'
    IN_PROGRESS = 'in_progress'
    FINISHED = 'finished'


class InvalidTransition(Exception):
    pass


_ALLOWED_TRANSITIONS = {
    SessionStatus.LOBBY: {SessionStatus.IN_PROGRESS},
    SessionStatus.IN_PROGRESS: {SessionStatus.FINISHED},
    SessionStatus.FINISHED: set(),
}


class SessionLifecycleService:
    """Unica responsabilidad: validar las transiciones de estado de una partida."""

    def transition(self, current: SessionStatus, target: SessionStatus) -> SessionStatus:
        if target not in _ALLOWED_TRANSITIONS[current]:
            raise InvalidTransition(f'No se puede pasar de {current.value} a {target.value}')
        return target
