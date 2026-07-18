from apps.game.domain.ladder import FixedLadderStrategy, LadderLevel
from apps.game.domain.scoring import ScoringService


def make_scoring():
    ladder = FixedLadderStrategy([
        LadderLevel(index=0, points=100),
        LadderLevel(index=1, points=200, is_checkpoint=True),
        LadderLevel(index=2, points=500),
    ])
    return ScoringService(ladder)


def test_correct_answer_awards_level_points():
    scoring = make_scoring()
    assert scoring.score_for_answer(level_index=2, is_correct=True) == 500


def test_incorrect_answer_falls_back_to_checkpoint():
    scoring = make_scoring()
    assert scoring.score_for_answer(level_index=2, is_correct=False) == 200


def test_incorrect_answer_before_any_checkpoint_scores_zero():
    scoring = make_scoring()
    assert scoring.score_for_answer(level_index=0, is_correct=False) == 0
