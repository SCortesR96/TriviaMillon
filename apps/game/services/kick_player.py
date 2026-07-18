from ..models import Player


class PlayerNotInSession(Exception):
    pass


class KickPlayer:
    """Expulsa a un jugador de la sala: borra su registro (sus respuestas caen en cascada)."""

    def execute(self, session_id: int, player_id: int) -> str:
        """Devuelve el channel_name que tenia el jugador, para poder cortar su WebSocket (o '' si no tenia)."""
        try:
            player = Player.objects.get(id=player_id, session_id=session_id)
        except Player.DoesNotExist:
            raise PlayerNotInSession(f'El jugador {player_id} no pertenece a esta sala')

        channel_name = player.channel_name
        player.delete()
        return channel_name
