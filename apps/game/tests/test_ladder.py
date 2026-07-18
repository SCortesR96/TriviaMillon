import pytest

from apps.game.domain.ladder import FixedLadderStrategy, LadderLevel


def make_ladder():
    return FixedLadderStrategy([
        LadderLevel(index=0, points=100, is_checkpoint=False),
        LadderLevel(index=1, points=200, is_checkpoint=False),
        LadderLevel(index=2, points=500, is_checkpoint=True),
        LadderLevel(index=3, points=1000, is_checkpoint=False),
    ])


def test_total_levels():
    assert make_ladder().total_levels() == 4


def test_points_for_level():
    ladder = make_ladder()
    assert ladder.points_for_level(0) == 100
    assert ladder.points_for_level(3) == 1000


def test_is_checkpoint():
    ladder = make_ladder()
    assert ladder.is_checkpoint(2) is True
    assert ladder.is_checkpoint(0) is False


def test_safe_points_before_checkpoint_reached():
    ladder = make_ladder()
    assert ladder.safe_points_before(3) == 500


def test_safe_points_before_no_checkpoint_reached():
    ladder = make_ladder()
    assert ladder.safe_points_before(1) == 0


def test_invalid_level_raises():
    ladder = make_ladder()
    with pytest.raises(ValueError):
        ladder.points_for_level(99)


def test_empty_levels_raises():
    with pytest.raises(ValueError):
        FixedLadderStrategy([])


def test_levels_are_sorted_by_index():
    ladder = FixedLadderStrategy([
        LadderLevel(index=1, points=200),
        LadderLevel(index=0, points=100),
    ])
    assert ladder.points_for_level(0) == 100
    assert ladder.points_for_level(1) == 200
