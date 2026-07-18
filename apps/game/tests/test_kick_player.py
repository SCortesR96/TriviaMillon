import pytest

from apps.game.models import Player, PlayerAnswer
from apps.game.services.kick_player import KickPlayer, PlayerNotInSession
from apps.game.services.start_question import StartQuestion
from apps.game.services.submit_answer import SubmitAnswer
from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db


def test_kicks_player_and_returns_channel_name(lobby_session):
    player = Player.objects.create(session=lobby_session, nickname='jugador1', channel_name='specific.channel!abc')

    channel_name = KickPlayer().execute(lobby_session.id, player.id)

    assert channel_name == 'specific.channel!abc'
    assert not Player.objects.filter(id=player.id).exists()


def test_kick_cascades_delete_of_answers(lobby_session):
    player = Player.objects.create(session=lobby_session, nickname='jugador1')
    StartQuestion().execute(lobby_session.id)
    correct_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=True)
    SubmitAnswer().execute(lobby_session.id, player.id, correct_option.id)

    KickPlayer().execute(lobby_session.id, player.id)

    assert PlayerAnswer.objects.filter(player_id=player.id).count() == 0


def test_kick_unknown_player_raises(lobby_session):
    with pytest.raises(PlayerNotInSession):
        KickPlayer().execute(lobby_session.id, player_id=999999)


def test_kick_player_from_a_different_session_raises(lobby_session, question_set, ladder_template):
    from apps.game.models import GameSession

    other_session = GameSession.objects.create(
        code='OTHER99', host_token='t', question_set=question_set, ladder_template=ladder_template,
    )
    player = Player.objects.create(session=other_session, nickname='jugador1')

    with pytest.raises(PlayerNotInSession):
        KickPlayer().execute(lobby_session.id, player.id)
