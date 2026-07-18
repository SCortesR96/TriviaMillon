import pytest

from apps.game.services.join_session import JoinSession, NicknameTaken, SessionNotJoinable

pytestmark = pytest.mark.django_db


def test_joins_lobby_session(lobby_session):
    player = JoinSession().execute(lobby_session.code, 'jugador1')

    assert player.session_id == lobby_session.id
    assert player.nickname == 'jugador1'
    assert player.score == 0


def test_rejects_unknown_code():
    with pytest.raises(SessionNotJoinable):
        JoinSession().execute('NOEXISTE', 'jugador1')


def test_rejects_join_after_session_started(in_progress_session):
    with pytest.raises(SessionNotJoinable):
        JoinSession().execute(in_progress_session.code, 'jugador1')


def test_rejects_duplicate_nickname_in_same_session(lobby_session):
    JoinSession().execute(lobby_session.code, 'jugador1')
    with pytest.raises(NicknameTaken):
        JoinSession().execute(lobby_session.code, 'jugador1')
