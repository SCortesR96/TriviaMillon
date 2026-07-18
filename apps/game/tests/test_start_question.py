import pytest

from apps.game.models import GameSession
from apps.game.services.start_question import SessionNotInLobby, StartQuestion

pytestmark = pytest.mark.django_db


def test_starts_session_and_returns_first_question(lobby_session):
    question = StartQuestion().execute(lobby_session.id)

    lobby_session.refresh_from_db()
    assert lobby_session.status == GameSession.Status.IN_PROGRESS
    assert lobby_session.current_level_index == 0
    assert question.text == 'Pregunta 0'


def test_rejects_starting_a_session_not_in_lobby(in_progress_session):
    with pytest.raises(SessionNotInLobby):
        StartQuestion().execute(in_progress_session.id)
