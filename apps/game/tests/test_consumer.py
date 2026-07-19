import json

import pytest
from channels.db import database_sync_to_async
from channels.testing import WebsocketCommunicator

from apps.game.consumers import GameConsumer
from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db(transaction=True)


async def test_ping_replies_with_pong_even_before_joining():
    communicator = WebsocketCommunicator(GameConsumer.as_asgi(), '/ws/game/')
    connected, _ = await communicator.connect()
    assert connected

    await communicator.send_to(text_data=json.dumps({'type': 'ping'}))
    ack = json.loads(await communicator.receive_from())

    assert ack['event'] == 'pong'
    await communicator.disconnect()


async def test_ping_replies_with_pong_after_joining(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    await host.send_to(text_data=json.dumps({'type': 'ping'}))
    ack = json.loads(await host.receive_from())

    assert ack['event'] == 'pong'
    await host.disconnect()


async def test_player_join_receives_confirmation(lobby_session, connect_and_join):
    player = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')

    ack = json.loads(await player.receive_from())

    assert ack['event'] == 'joined'
    assert ack['role'] == 'player'
    assert ack['player_id'] is not None
    await player.disconnect()


async def test_join_unknown_code_returns_error(lobby_session, connect_and_join):
    player = await connect_and_join(role='player', code='NOEXISTE', nickname='jugador1')

    ack = json.loads(await player.receive_from())

    assert ack['event'] == 'error'
    await player.disconnect()


async def test_host_join_with_wrong_token_returns_error(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token='wrong-token')

    ack = json.loads(await host.receive_from())

    assert ack['event'] == 'error'
    await host.disconnect()


async def test_rejoin_with_same_nickname_reconnects_to_existing_player(lobby_session, connect_and_join):
    first = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    first_ack = json.loads(await first.receive_from())
    await first.disconnect()

    second = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    second_ack = json.loads(await second.receive_from())

    assert second_ack['player_id'] == first_ack['player_id']
    await second.disconnect()


async def test_full_game_flow_between_host_and_player(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined (host)

    player = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    await player.receive_from()  # joined (player)
    await player.receive_from()  # player_joined: el propio jugador ya esta en el grupo cuando se difunde
    await host.receive_from()  # player_joined, difundido al host

    await host.send_to(text_data=json.dumps({'type': 'start'}))
    host_started = json.loads(await host.receive_from())
    player_started = json.loads(await player.receive_from())
    assert host_started['event'] == 'question_started'
    assert player_started['event'] == 'question_started'
    assert all('is_correct' not in option for option in player_started['options'])

    correct_option = await database_sync_to_async(AnswerOption.objects.get)(
        question__text='Pregunta 0', is_correct=True,
    )
    await player.send_to(text_data=json.dumps({'type': 'answer', 'option_id': correct_option.id}))
    player_ack = json.loads(await player.receive_from())
    assert player_ack['event'] == 'answer_received'
    await player.receive_from()  # player_answered: tambien se difunde de vuelta a quien respondio
    host_notice = json.loads(await host.receive_from())
    assert host_notice['event'] == 'player_answered'

    await host.send_to(text_data=json.dumps({'type': 'reveal'}))
    host_reveal = json.loads(await host.receive_from())
    player_reveal = json.loads(await player.receive_from())
    assert host_reveal['event'] == player_reveal['event'] == 'answer_revealed'
    assert host_reveal['correct_option_id'] == correct_option.id

    await host.send_to(text_data=json.dumps({'type': 'next'}))
    host_next = json.loads(await host.receive_from())
    player_next = json.loads(await player.receive_from())
    assert host_next['event'] == player_next['event'] == 'question_started'

    await host.send_to(text_data=json.dumps({'type': 'next'}))
    host_end = json.loads(await host.receive_from())
    player_end = json.loads(await player.receive_from())
    assert host_end['event'] == player_end['event'] == 'game_ended'
    assert host_end['leaderboard'][0]['nickname'] == 'jugador1'

    await host.disconnect()
    await player.disconnect()


async def test_end_before_start_returns_error(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    await host.send_to(text_data=json.dumps({'type': 'end'}))
    ack = json.loads(await host.receive_from())

    assert ack['event'] == 'error'
    await host.disconnect()
