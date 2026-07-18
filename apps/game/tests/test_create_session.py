import pytest

from apps.game.models import GameSession
from apps.game.services.create_session import CreateSession

pytestmark = pytest.mark.django_db


def test_creates_session_in_lobby(question_set, ladder_template):
    session = CreateSession().execute(question_set.id, ladder_template.id, host_token='host-1')

    assert session.status == GameSession.Status.LOBBY
    assert session.question_set_id == question_set.id
    assert session.ladder_template_id == ladder_template.id
    assert session.current_level_index == 0
    assert len(session.code) == 6


def test_generates_unique_codes(question_set, ladder_template):
    session_a = CreateSession().execute(question_set.id, ladder_template.id, host_token='host-1')
    session_b = CreateSession().execute(question_set.id, ladder_template.id, host_token='host-2')

    assert session_a.code != session_b.code
