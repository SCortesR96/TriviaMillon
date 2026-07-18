import pytest

from apps.game.models import GameSession, LadderTemplate, PrizeLevel
from apps.questions.models import AnswerOption, Question, QuestionSet


@pytest.fixture
def question_set(db):
    qs = QuestionSet.objects.create(name='Set de prueba')
    for i in range(2):
        question = Question.objects.create(question_set=qs, text=f'Pregunta {i}', order=i)
        AnswerOption.objects.create(question=question, text='correcta', is_correct=True, order=0)
        AnswerOption.objects.create(question=question, text='incorrecta', is_correct=False, order=1)
    return qs


@pytest.fixture
def ladder_template(db):
    ladder = LadderTemplate.objects.create(name='Escalera de prueba')
    PrizeLevel.objects.create(ladder_template=ladder, index=0, points=100, is_checkpoint=True)
    PrizeLevel.objects.create(ladder_template=ladder, index=1, points=200, is_checkpoint=False)
    return ladder


@pytest.fixture
def lobby_session(question_set, ladder_template):
    return GameSession.objects.create(
        code='ABC123',
        host_token='host-token',
        question_set=question_set,
        ladder_template=ladder_template,
    )


@pytest.fixture
def in_progress_session(lobby_session):
    lobby_session.status = GameSession.Status.IN_PROGRESS
    lobby_session.save(update_fields=['status'])
    return lobby_session
