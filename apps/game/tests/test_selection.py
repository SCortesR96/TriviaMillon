from apps.game.domain.entities import AnswerOption, Question
from apps.game.domain.selection import QuestionSelectionService


def make_question(id, order=None):
    return Question(
        id=id,
        text=f'Pregunta {id}',
        options=[AnswerOption(id=1, text='A', is_correct=True)],
        order=order,
    )


def test_orders_questions_by_explicit_order():
    service = QuestionSelectionService([
        make_question(1, order=2),
        make_question(2, order=1),
        make_question(3, order=0),
    ])
    assert service.question_at(0).id == 3
    assert service.question_at(1).id == 2
    assert service.question_at(2).id == 1


def test_falls_back_to_id_when_order_missing():
    service = QuestionSelectionService([make_question(2), make_question(1)])
    assert service.question_at(0).id == 1
    assert service.question_at(1).id == 2


def test_total_questions():
    service = QuestionSelectionService([make_question(1), make_question(2)])
    assert service.total_questions() == 2


def test_question_at_out_of_range_returns_none():
    service = QuestionSelectionService([make_question(1)])
    assert service.question_at(5) is None
    assert service.question_at(-1) is None
