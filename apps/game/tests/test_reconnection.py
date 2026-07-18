import json

import pytest
from channels.db import database_sync_to_async

from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db(transaction=True)


async def test_reconnect_during_lobby_gets_no_active_question(lobby_session, connect_and_join):
    first = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    await first.receive_from()  # joined
    await first.disconnect()

    second = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    await second.receive_from()  # joined
    await second.receive_from()  # player_joined
    assert await second.receive_nothing(timeout=0.2)
    await second.disconnect()


async def test_reconnect_mid_question_receives_active_question(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    player = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    await player.receive_from()  # joined
    await player.receive_from()  # player_joined (echo)
    await host.receive_from()  # player_joined

    await host.send_to(text_data=json.dumps({'type': 'start'}))
    await host.receive_from()  # question_started (host)
    await player.receive_from()  # question_started (player, primera vez)

    # se corta la señal antes de contestar
    await player.disconnect()

    reconnected = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    ack = json.loads(await reconnected.receive_from())  # joined
    assert ack['player_id'] is not None
    catch_up = json.loads(await reconnected.receive_from())  # question_started de reconexion (antes del broadcast)
    await reconnected.receive_from()  # player_joined (echo)
    await host.receive_from()  # player_joined (rebroadcast por la "reconexion")

    assert catch_up['event'] == 'question_started'
    assert catch_up['text'] == 'Pregunta 0'
    assert catch_up['already_answered'] is False

    await host.disconnect()
    await reconnected.disconnect()


async def test_reconnect_after_answering_flags_already_answered(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined

    player = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    ack = json.loads(await player.receive_from())  # joined
    player_id = ack['player_id']
    await player.receive_from()  # player_joined (echo)
    await host.receive_from()  # player_joined

    await host.send_to(text_data=json.dumps({'type': 'start'}))
    await host.receive_from()  # question_started (host)
    await player.receive_from()  # question_started (player)

    correct_option = await database_sync_to_async(AnswerOption.objects.get)(
        question__text='Pregunta 0', is_correct=True,
    )
    await player.send_to(text_data=json.dumps({'type': 'answer', 'option_id': correct_option.id}))
    await player.receive_from()  # answer_received
    await player.receive_from()  # player_answered (echo)
    await host.receive_from()  # player_answered

    await player.disconnect()  # se pierde la señal justo despues de responder

    reconnected = await connect_and_join(role='player', code=lobby_session.code, nickname='jugador1')
    ack2 = json.loads(await reconnected.receive_from())  # joined
    assert ack2['player_id'] == player_id
    catch_up = json.loads(await reconnected.receive_from())  # question_started de reconexion
    await reconnected.receive_from()  # player_joined (echo)
    await host.receive_from()  # player_joined (rebroadcast)

    assert catch_up['already_answered'] is True

    await host.disconnect()
    await reconnected.disconnect()
