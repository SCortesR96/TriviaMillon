import pytest

from apps.game.domain.lifecycle import InvalidTransition
from apps.game.models import GameSession
from apps.game.services.end_session import EndSession

pytestmark = pytest.mark.django_db


def test_ends_an_in_progress_session(in_progress_session):
    session = EndSession().execute(in_progress_session.id)

    assert session.status == GameSession.Status.FINISHED


def test_cannot_end_a_session_still_in_lobby(lobby_session):
    with pytest.raises(InvalidTransition):
        EndSession().execute(lobby_session.id)


def test_cannot_end_an_already_finished_session(in_progress_session):
    EndSession().execute(in_progress_session.id)
    with pytest.raises(InvalidTransition):
        EndSession().execute(in_progress_session.id)
