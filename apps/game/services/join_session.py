from django.db import IntegrityError

from ..models import GameSession, Player


class SessionNotJoinable(Exception):
    pass


class NicknameTaken(Exception):
    pass


class JoinSession:
    """Un jugador se une a una sala existente por codigo de sala + nickname."""

    def execute(self, code: str, nickname: str) -> Player:
        try:
            session = GameSession.objects.get(code=code)
        except GameSession.DoesNotExist:
            raise SessionNotJoinable(f'No existe una sala con codigo {code!r}')

        if session.status != GameSession.Status.LOBBY:
            raise SessionNotJoinable('La sala ya inicio o termino, no se puede unir')

        try:
            return Player.objects.create(session=session, nickname=nickname)
        except IntegrityError:
            raise NicknameTaken(f'El nickname {nickname!r} ya esta en uso en esta sala')
