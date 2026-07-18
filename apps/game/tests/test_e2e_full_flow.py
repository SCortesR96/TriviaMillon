import json

import pytest
from channels.db import database_sync_to_async

from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db(transaction=True)


async def _drain_broadcasts(*communicators, count=1):
    """Descarta `count` mensajes de cada comunicador (ack propio + difusiones cruzadas)."""
    for communicator in communicators:
        for _ in range(count):
            await communicator.receive_from()


async def test_full_flow_create_join_several_players_play_and_end(lobby_session, connect_and_join):
    host = await connect_and_join(role='host', code=lobby_session.code, host_token=lobby_session.host_token)
    await host.receive_from()  # joined (host)

    players = {}
    for nickname in ('ana', 'beto', 'caro'):
        communicator = await connect_and_join(role='player', code=lobby_session.code, nickname=nickname)
        ack = json.loads(await communicator.receive_from())  # joined
        players[nickname] = {'ws': communicator, 'id': ack['player_id']}
        await communicator.receive_from()  # player_joined (echo a si mismo)
        await host.receive_from()  # player_joined difundido al host
        # cada jugador previo tambien recibe el player_joined de este nuevo jugador
        for other_nickname, other in players.items():
            if other_nickname != nickname:
                await other['ws'].receive_from()

    await host.send_to(text_data=json.dumps({'type': 'start'}))
    await host.receive_from()  # question_started (host)
    for player in players.values():
        await player['ws'].receive_from()  # question_started

    q0_correct = await database_sync_to_async(AnswerOption.objects.get)(
        question__text='Pregunta 0', is_correct=True,
    )
    q0_wrong = await database_sync_to_async(AnswerOption.objects.get)(
        question__text='Pregunta 0', is_correct=False,
    )
    # ana y beto responden bien la primera pregunta, caro falla
    for nickname, option in (('ana', q0_correct), ('beto', q0_correct), ('caro', q0_wrong)):
        ws = players[nickname]['ws']
        await ws.send_to(text_data=json.dumps({'type': 'answer', 'option_id': option.id}))
        await ws.receive_from()  # answer_received
        await ws.receive_from()  # player_answered (echo)
        await host.receive_from()  # player_answered difundido al host
        for other_nickname, other in players.items():
            if other_nickname != nickname:
                await other['ws'].receive_from()  # player_answered difundido a los demas

    await host.send_to(text_data=json.dumps({'type': 'reveal'}))
    await host.receive_from()  # answer_revealed
    for player in players.values():
        await player['ws'].receive_from()  # answer_revealed

    await host.send_to(text_data=json.dumps({'type': 'next'}))
    await host.receive_from()  # question_started (pregunta 1)
    for player in players.values():
        await player['ws'].receive_from()

    q1_correct = await database_sync_to_async(AnswerOption.objects.get)(
        question__text='Pregunta 1', is_correct=True,
    )
    q1_wrong = await database_sync_to_async(AnswerOption.objects.get)(
        question__text='Pregunta 1', is_correct=False,
    )
    # ana responde bien de nuevo, beto y caro fallan
    for nickname, option in (('ana', q1_correct), ('beto', q1_wrong), ('caro', q1_wrong)):
        ws = players[nickname]['ws']
        await ws.send_to(text_data=json.dumps({'type': 'answer', 'option_id': option.id}))
        await ws.receive_from()  # answer_received
        await ws.receive_from()  # player_answered (echo)
        await host.receive_from()
        for other_nickname, other in players.items():
            if other_nickname != nickname:
                await other['ws'].receive_from()

    await host.send_to(text_data=json.dumps({'type': 'next'}))  # no quedan mas preguntas -> termina
    host_end = json.loads(await host.receive_from())
    player_ends = {}
    for nickname, player in players.items():
        player_ends[nickname] = json.loads(await player['ws'].receive_from())

    assert host_end['event'] == 'game_ended'
    # ana: 100 (Q0 correcta) + 200 (Q1 correcta) = 300
    # beto: 100 (Q0 correcta) + 100 (Q1 fallada, checkpoint ya alcanzado) = 200
    # caro: 0 (Q0 fallada, sin checkpoint alcanzado aun) + 100 (Q1 fallada) = 100
    leaderboard_by_nick = {p['nickname']: p['score'] for p in host_end['leaderboard']}
    assert leaderboard_by_nick == {'ana': 300, 'beto': 200, 'caro': 100}
    # el leaderboard viene ordenado de mayor a menor puntaje
    assert [p['nickname'] for p in host_end['leaderboard']] == ['ana', 'beto', 'caro']
    for nickname in players:
        assert player_ends[nickname]['event'] == 'game_ended'
        assert player_ends[nickname]['leaderboard'] == host_end['leaderboard']

    await host.disconnect()
    for player in players.values():
        await player['ws'].disconnect()
