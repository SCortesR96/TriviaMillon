import json

import pytest
from channels.db import database_sync_to_async

from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db(transaction=True)


async def test_pause_and_resume_broadcast_to_everyone(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    player = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    await player.receive_from()  # joined
    await player.receive_from()  # player_joined (echo)
    await host.receive_from()  # player_joined

    await host.send_to(text_data=json.dumps({'type': 'start'}))
    await host.receive_from()  # question_started
    await player.receive_from()  # question_started

    await host.send_to(text_data=json.dumps({'type': 'pause'}))
    host_paused = json.loads(await host.receive_from())
    player_paused = json.loads(await player.receive_from())
    assert host_paused['event'] == player_paused['event'] == 'paused'

    await host.send_to(text_data=json.dumps({'type': 'resume'}))
    host_resumed = json.loads(await host.receive_from())
    player_resumed = json.loads(await player.receive_from())
    assert host_resumed['event'] == player_resumed['event'] == 'resumed'

    await host.disconnect()
    await player.disconnect()


async def test_answer_rejected_while_paused(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    player = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    await player.receive_from()  # joined
    await player.receive_from()  # player_joined (echo)
    await host.receive_from()  # player_joined

    await host.send_to(text_data=json.dumps({'type': 'start'}))
    await host.receive_from()  # question_started
    await player.receive_from()  # question_started

    await host.send_to(text_data=json.dumps({'type': 'pause'}))
    await host.receive_from()  # paused
    await player.receive_from()  # paused

    correct_option = await database_sync_to_async(AnswerOption.objects.get)(
        question__text='Pregunta 0', is_correct=True,
    )
    await player.send_to(text_data=json.dumps({'type': 'answer', 'option_id': correct_option.id}))
    ack = json.loads(await player.receive_from())

    assert ack['event'] == 'error'

    await host.disconnect()
    await player.disconnect()


async def test_host_can_skip_question_without_revealing(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    await host.send_to(text_data=json.dumps({'type': 'start'}))
    await host.receive_from()  # question_started (Pregunta 0)

    await host.send_to(text_data=json.dumps({'type': 'next'}))  # saltar sin revelar
    skip_result = json.loads(await host.receive_from())

    assert skip_result['event'] == 'question_started'
    assert skip_result['text'] == 'Pregunta 1'

    await host.disconnect()


async def test_kick_disconnects_the_player_and_updates_the_list(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    player = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    ack = json.loads(await player.receive_from())  # joined
    player_id = ack['player_id']
    await player.receive_from()  # player_joined (echo)
    await host.receive_from()  # player_joined

    await host.send_to(text_data=json.dumps({'type': 'kick', 'player_id': player_id}))

    kicked_msg = json.loads(await player.receive_from())
    assert kicked_msg['event'] == 'kicked'

    host_update = json.loads(await host.receive_from())
    assert host_update['event'] == 'player_joined'
    assert host_update['players'] == []

    await host.disconnect()


async def test_kick_unknown_player_returns_error(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    await host.send_to(text_data=json.dumps({'type': 'kick', 'player_id': 999999}))
    ack = json.loads(await host.receive_from())

    assert ack['event'] == 'error'
    await host.disconnect()
