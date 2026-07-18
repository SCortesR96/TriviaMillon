import pytest

from apps.game.services.get_active_question import GetActiveQuestion
from apps.game.services.join_session import JoinSession
from apps.game.services.start_question import StartQuestion
from apps.game.services.submit_answer import SubmitAnswer
from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db


def test_returns_none_while_in_lobby(lobby_session):
    assert GetActiveQuestion().execute(lobby_session.id) is None


def test_returns_current_question_when_in_progress(lobby_session):
    StartQuestion().execute(lobby_session.id)

    result = GetActiveQuestion().execute(lobby_session.id)

    assert result is not None
    question, already_answered = result
    assert question.text == 'Pregunta 0'
    assert already_answered is False


def test_marks_already_answered_for_that_player(lobby_session):
    player = JoinSession().execute(lobby_session.code, 'jugador1')
    StartQuestion().execute(lobby_session.id)
    correct_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=True)
    SubmitAnswer().execute(lobby_session.id, player.id, correct_option.id)

    _, already_answered = GetActiveQuestion().execute(lobby_session.id, player.id)

    assert already_answered is True


def test_not_answered_for_a_different_player(lobby_session):
    answerer = JoinSession().execute(lobby_session.code, 'jugador1')
    other = JoinSession().execute(lobby_session.code, 'jugador2')
    StartQuestion().execute(lobby_session.id)
    correct_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=True)
    SubmitAnswer().execute(lobby_session.id, answerer.id, correct_option.id)

    _, already_answered = GetActiveQuestion().execute(lobby_session.id, other.id)

    assert already_answered is False


def test_returns_none_when_no_more_questions(lobby_session):
    from apps.game.services.advance_question import AdvanceQuestion

    StartQuestion().execute(lobby_session.id)
    AdvanceQuestion().execute(lobby_session.id)
    AdvanceQuestion().execute(lobby_session.id)  # ya termino

    assert GetActiveQuestion().execute(lobby_session.id) is None
