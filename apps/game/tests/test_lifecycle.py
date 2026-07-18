import pytest

from apps.game.domain.lifecycle import InvalidTransition, SessionLifecycleService, SessionStatus


def test_lobby_to_in_progress_is_allowed():
    service = SessionLifecycleService()
    assert service.transition(SessionStatus.LOBBY, SessionStatus.IN_PROGRESS) == SessionStatus.IN_PROGRESS


def test_in_progress_to_finished_is_allowed():
    service = SessionLifecycleService()
    assert service.transition(SessionStatus.IN_PROGRESS, SessionStatus.FINISHED) == SessionStatus.FINISHED


def test_lobby_to_finished_is_not_allowed():
    service = SessionLifecycleService()
    with pytest.raises(InvalidTransition):
        service.transition(SessionStatus.LOBBY, SessionStatus.FINISHED)


def test_finished_is_terminal():
    service = SessionLifecycleService()
    with pytest.raises(InvalidTransition):
        service.transition(SessionStatus.FINISHED, SessionStatus.IN_PROGRESS)


def test_cannot_restart_in_progress():
    service = SessionLifecycleService()
    with pytest.raises(InvalidTransition):
        service.transition(SessionStatus.IN_PROGRESS, SessionStatus.LOBBY)
