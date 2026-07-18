import pytest

from apps.game.models import Player
from apps.game.services.pause_session import PauseSession, ResumeSession, SessionNotInProgress
from apps.game.services.start_question import StartQuestion
from apps.game.services.submit_answer import SessionPaused, SubmitAnswer
from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db


def test_pauses_an_in_progress_session(in_progress_session):
    session = PauseSession().execute(in_progress_session.id)

    assert session.is_paused is True


def test_cannot_pause_a_lobby_session(lobby_session):
    with pytest.raises(SessionNotInProgress):
        PauseSession().execute(lobby_session.id)


def test_resumes_a_paused_session(in_progress_session):
    PauseSession().execute(in_progress_session.id)

    session = ResumeSession().execute(in_progress_session.id)

    assert session.is_paused is False


def test_submit_answer_rejected_while_paused(lobby_session):
    player = Player.objects.create(session=lobby_session, nickname='jugador1')
    StartQuestion().execute(lobby_session.id)
    PauseSession().execute(lobby_session.id)
    correct_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=True)

    with pytest.raises(SessionPaused):
        SubmitAnswer().execute(lobby_session.id, player.id, correct_option.id)
