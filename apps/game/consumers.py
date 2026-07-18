import json

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .domain.entities import Question as DomainQuestion
from .domain.lifecycle import InvalidTransition
from .models import GameSession, Player
from .services.advance_question import AdvanceQuestion
from .services.end_session import EndSession
from .services.join_session import JoinSession, NicknameTaken, SessionNotJoinable
from .services.reveal_answer import NoActiveQuestion as RevealNoActiveQuestion
from .services.reveal_answer import RevealAnswer
from .services.start_question import SessionNotInLobby, StartQuestion
from .services.submit_answer import AlreadyAnswered, NoActiveQuestion, SubmitAnswer


class PingConsumer(AsyncWebsocketConsumer):
    """Consumer de prueba para validar el transporte WebSocket + Redis de punta a punta."""

    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({'type': 'pong', 'echo': data}))


def _group_name(code: str) -> str:
    return f'game_{code}'


def _question_payload(question: DomainQuestion) -> dict:
    return {
        'question_id': question.id,
        'text': question.text,
        'options': [{'id': o.id, 'text': o.text} for o in question.options],
    }


class GameConsumer(AsyncWebsocketConsumer):
    """Consumer delgado: traduce eventos WebSocket a llamadas a los use cases de apps/game/services.

    Un mismo endpoint sirve tanto al host (proyector) como a los jugadores (celular);
    el primer mensaje ('join') decide el rol y la sala. Sin logica de negocio aqui:
    cada evento delega en un use case y difunde el resultado al grupo de la sala.
    """

    async def connect(self):
        await self.accept()
        self.session_id = None
        self.group_name = None
        self.role = None
        self.player_id = None

    async def disconnect(self, close_code):
        if self.group_name:
            await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        message = json.loads(text_data)
        handler = getattr(self, f'_handle_{message.get("type")}', None)
        if handler is None:
            await self._send_error(f'Tipo de mensaje desconocido: {message.get("type")!r}')
            return
        try:
            await handler(message)
        except KeyError as exc:
            await self._send_error(f'Falta el campo {exc} en el mensaje')

    # -- handlers de eventos entrantes --

    async def _handle_join(self, message):
        code = message['code']
        role = message.get('role', 'player')
        session = await self._get_session_by_code(code)
        if session is None:
            await self._send_error(f'No existe la sala {code!r}')
            return

        if role == 'host':
            if message.get('host_token') != session.host_token:
                await self._send_error('host_token invalido')
                return
            self.session_id, self.group_name, self.role = session.id, _group_name(code), 'host'
            await self.channel_layer.group_add(self.group_name, self.channel_name)
            await self.send(text_data=json.dumps({
                'event': 'joined', 'role': 'host', 'status': session.status,
                'players': await self._get_players(session.id),
            }))
            return

        nickname = message['nickname']
        existing = await self._get_player_by_nickname(session.id, nickname)
        if existing is not None:
            player_id = existing.id  # reconexion: mismo nickname ya registrado en la sala
        else:
            try:
                player = await self._join_session(code, nickname)
            except (SessionNotJoinable, NicknameTaken) as exc:
                await self._send_error(str(exc))
                return
            player_id = player.id

        self.session_id, self.group_name, self.role, self.player_id = (
            session.id, _group_name(code), 'player', player_id,
        )
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.send(text_data=json.dumps({
            'event': 'joined', 'role': 'player', 'player_id': player_id, 'status': session.status,
        }))
        await self._broadcast('player_joined', {'players': await self._get_players(session.id)})

    async def _handle_start(self, message):
        if self.role != 'host':
            return
        try:
            question = await self._start_question(self.session_id)
        except SessionNotInLobby as exc:
            await self._send_error(str(exc))
            return
        await self._broadcast('question_started', _question_payload(question))

    async def _handle_answer(self, message):
        if self.role != 'player' or self.player_id is None:
            return
        try:
            await self._submit_answer(
                self.session_id, self.player_id, message['option_id'], message.get('response_time_ms'),
            )
        except (NoActiveQuestion, AlreadyAnswered) as exc:
            await self._send_error(str(exc))
            return
        await self.send(text_data=json.dumps({'event': 'answer_received'}))
        await self._broadcast('player_answered', {'player_id': self.player_id})

    async def _handle_reveal(self, message):
        if self.role != 'host':
            return
        try:
            result = await self._reveal_answer(self.session_id)
        except RevealNoActiveQuestion as exc:
            await self._send_error(str(exc))
            return
        await self._broadcast('answer_revealed', result)

    async def _handle_next(self, message):
        if self.role != 'host':
            return
        question = await self._advance_question(self.session_id)
        if question is None:
            await self._broadcast('game_ended', {'leaderboard': await self._get_players(self.session_id)})
        else:
            await self._broadcast('question_started', _question_payload(question))

    async def _handle_end(self, message):
        if self.role != 'host':
            return
        try:
            await self._end_session(self.session_id)
        except InvalidTransition as exc:
            await self._send_error(str(exc))
            return
        await self._broadcast('game_ended', {'leaderboard': await self._get_players(self.session_id)})

    # -- difusion a la sala y helpers de envio --

    async def _broadcast(self, event, payload):
        await self.channel_layer.group_send(self.group_name, {
            'type': 'game_event', 'event': event, 'payload': payload,
        })

    async def game_event(self, message):
        await self.send(text_data=json.dumps({'event': message['event'], **message['payload']}))

    async def _send_error(self, detail):
        await self.send(text_data=json.dumps({'event': 'error', 'detail': detail}))

    # -- acceso a datos, envuelto para el event loop async de Channels --

    @database_sync_to_async
    def _get_session_by_code(self, code):
        return GameSession.objects.filter(code=code).first()

    @database_sync_to_async
    def _get_player_by_nickname(self, session_id, nickname):
        return Player.objects.filter(session_id=session_id, nickname=nickname).first()

    @database_sync_to_async
    def _get_players(self, session_id):
        players = Player.objects.filter(session_id=session_id).order_by('-score', 'joined_at')
        return [{'id': p.id, 'nickname': p.nickname, 'score': p.score} for p in players]

    @database_sync_to_async
    def _join_session(self, code, nickname):
        return JoinSession().execute(code, nickname)

    @database_sync_to_async
    def _start_question(self, session_id):
        return StartQuestion().execute(session_id)

    @database_sync_to_async
    def _submit_answer(self, session_id, player_id, option_id, response_time_ms):
        return SubmitAnswer().execute(session_id, player_id, option_id, response_time_ms)

    @database_sync_to_async
    def _reveal_answer(self, session_id):
        return RevealAnswer().execute(session_id)

    @database_sync_to_async
    def _advance_question(self, session_id):
        return AdvanceQuestion().execute(session_id)

    @database_sync_to_async
    def _end_session(self, session_id):
        return EndSession().execute(session_id)
