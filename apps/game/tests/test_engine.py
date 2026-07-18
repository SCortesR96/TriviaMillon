import pytest

from apps.game.domain.engine import GameEngine
from apps.game.domain.entities import AnswerOption, Question
from apps.game.domain.ladder import FixedLadderStrategy, LadderLevel


def make_engine():
    questions = [
        Question(
            id=1, order=0, text='Q1',
            options=[
                AnswerOption(id=10, text='correcta', is_correct=True),
                AnswerOption(id=11, text='incorrecta', is_correct=False),
            ],
        ),
        Question(
            id=2, order=1, text='Q2',
            options=[
                AnswerOption(id=20, text='correcta', is_correct=True),
                AnswerOption(id=21, text='incorrecta', is_correct=False),
            ],
        ),
    ]
    ladder = FixedLadderStrategy([
        LadderLevel(index=0, points=100, is_checkpoint=True),
        LadderLevel(index=1, points=200),
    ])
    return GameEngine(questions, ladder)


def test_starts_in_lobby_and_moves_to_in_progress():
    from apps.game.domain.lifecycle import SessionStatus

    engine = make_engine()
    assert engine.status == SessionStatus.LOBBY
    engine.start()
    assert engine.status == SessionStatus.IN_PROGRESS


def test_current_question_is_first_by_order():
    engine = make_engine()
    assert engine.current_question().id == 1


def test_submit_correct_answer_awards_level_points():
    engine = make_engine()
    engine.start()
    assert engine.submit_answer(10) == 100


def test_submit_incorrect_answer_falls_back_to_safe_points():
    engine = make_engine()
    engine.start()
    engine.advance()  # nivel 1, ya con checkpoint superado
    assert engine.submit_answer(21) == 100


def test_submit_answer_without_active_question_raises():
    engine = make_engine()
    engine.start()
    engine.advance()
    engine.advance()  # ya no quedan preguntas
    with pytest.raises(ValueError):
        engine.submit_answer(10)


def test_advance_ends_game_and_finishes_session():
    from apps.game.domain.lifecycle import SessionStatus

    engine = make_engine()
    engine.start()
    assert engine.advance().id == 2
    assert engine.is_over() is False
    assert engine.advance() is None
    assert engine.is_over() is True
    assert engine.status == SessionStatus.FINISHED
