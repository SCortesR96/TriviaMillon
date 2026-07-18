import pytest

from apps.game.models import GameSession
from apps.game.services.advance_question import AdvanceQuestion
from apps.game.services.start_question import StartQuestion

pytestmark = pytest.mark.django_db


def test_advances_to_next_question(lobby_session):
    StartQuestion().execute(lobby_session.id)

    next_question = AdvanceQuestion().execute(lobby_session.id)

    lobby_session.refresh_from_db()
    assert next_question.text == 'Pregunta 1'
    assert lobby_session.current_level_index == 1
    assert lobby_session.status == GameSession.Status.IN_PROGRESS


def test_finishes_session_when_no_more_questions(lobby_session):
    StartQuestion().execute(lobby_session.id)
    AdvanceQuestion().execute(lobby_session.id)  # -> Pregunta 1

    next_question = AdvanceQuestion().execute(lobby_session.id)  # ya no quedan preguntas

    lobby_session.refresh_from_db()
    assert next_question is None
    assert lobby_session.status == GameSession.Status.FINISHED
