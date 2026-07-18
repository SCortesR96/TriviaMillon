import pytest

from apps.game.infrastructure.django_repositories import (
    DjangoPlayerRepository,
    DjangoQuestionRepository,
    DjangoSessionRepository,
    build_ladder_strategy,
)
from apps.game.models import Player

pytestmark = pytest.mark.django_db


def test_question_repository_maps_orm_to_domain_entities(question_set):
    questions = DjangoQuestionRepository().get_questions_for_set(question_set.id)

    assert len(questions) == 2
    first = next(q for q in questions if q.text == 'Pregunta 0')
    assert first.order == 0
    assert len(first.options) == 2
    assert sum(1 for o in first.options if o.is_correct) == 1


def test_ladder_strategy_reflects_prize_levels(ladder_template):
    ladder = build_ladder_strategy(ladder_template.id)

    assert ladder.total_levels() == 2
    assert ladder.points_for_level(0) == 100
    assert ladder.is_checkpoint(0) is True
    assert ladder.points_for_level(1) == 200
    assert ladder.is_checkpoint(1) is False


def test_session_repository_reads_and_writes_status(lobby_session):
    from apps.game.domain.lifecycle import SessionStatus

    repo = DjangoSessionRepository()
    assert repo.get_status(lobby_session.id) == SessionStatus.LOBBY

    repo.save_status(lobby_session.id, SessionStatus.IN_PROGRESS)
    lobby_session.refresh_from_db()
    assert lobby_session.status == SessionStatus.IN_PROGRESS.value


def test_session_repository_reads_and_writes_current_level_index(lobby_session):
    repo = DjangoSessionRepository()
    assert repo.get_current_level_index(lobby_session.id) == 0

    repo.save_current_level_index(lobby_session.id, 1)
    lobby_session.refresh_from_db()
    assert lobby_session.current_level_index == 1


def test_player_repository_add_points_and_get_score(lobby_session):
    player = Player.objects.create(session=lobby_session, nickname='jugador1')
    repo = DjangoPlayerRepository()

    repo.add_points(player.id, 100)
    repo.add_points(player.id, 50)

    assert repo.get_score(player.id) == 150
