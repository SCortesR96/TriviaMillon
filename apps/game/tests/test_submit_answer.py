import pytest

from apps.game.models import Player
from apps.game.services.join_session import JoinSession
from apps.game.services.start_question import StartQuestion
from apps.game.services.submit_answer import AlreadyAnswered, NoActiveQuestion, SubmitAnswer
from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db


def _start_with_player(lobby_session):
    player = JoinSession().execute(lobby_session.code, 'jugador1')
    StartQuestion().execute(lobby_session.id)
    return player


def test_correct_answer_awards_level_points(lobby_session):
    player = _start_with_player(lobby_session)
    correct_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=True)

    answer = SubmitAnswer().execute(lobby_session.id, player.id, correct_option.id)

    assert answer.points_awarded == 100
    player.refresh_from_db()
    assert player.score == 100


def test_incorrect_answer_awards_safe_points(lobby_session):
    player = _start_with_player(lobby_session)
    wrong_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=False)

    answer = SubmitAnswer().execute(lobby_session.id, player.id, wrong_option.id)

    assert answer.points_awarded == 0  # nivel 0 aun no supera ningun checkpoint
    player.refresh_from_db()
    assert player.score == 0


def test_cannot_answer_same_question_twice(lobby_session):
    player = _start_with_player(lobby_session)
    correct_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=True)

    SubmitAnswer().execute(lobby_session.id, player.id, correct_option.id)
    with pytest.raises(AlreadyAnswered):
        SubmitAnswer().execute(lobby_session.id, player.id, correct_option.id)


def test_raises_when_no_active_question(lobby_session):
    player = Player.objects.create(session=lobby_session, nickname='jugador1')
    # current_level_index mas alla de la ultima pregunta: la partida ya no tiene pregunta activa
    lobby_session.current_level_index = 2
    lobby_session.save(update_fields=['current_level_index'])

    with pytest.raises(NoActiveQuestion):
        SubmitAnswer().execute(lobby_session.id, player.id, option_id=999)
