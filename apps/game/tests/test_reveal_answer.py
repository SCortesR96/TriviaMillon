import pytest

from apps.game.services.join_session import JoinSession
from apps.game.services.reveal_answer import NoActiveQuestion, RevealAnswer
from apps.game.services.start_question import StartQuestion
from apps.game.services.submit_answer import SubmitAnswer
from apps.questions.models import AnswerOption

pytestmark = pytest.mark.django_db


def test_reveals_correct_option_and_player_answers(lobby_session):
    player1 = JoinSession().execute(lobby_session.code, 'jugador1')
    player2 = JoinSession().execute(lobby_session.code, 'jugador2')
    StartQuestion().execute(lobby_session.id)

    correct_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=True)
    wrong_option = AnswerOption.objects.get(question__text='Pregunta 0', is_correct=False)
    SubmitAnswer().execute(lobby_session.id, player1.id, correct_option.id)
    SubmitAnswer().execute(lobby_session.id, player2.id, wrong_option.id)

    result = RevealAnswer().execute(lobby_session.id)

    assert result['correct_option_id'] == correct_option.id
    answers_by_nick = {a['nickname']: a for a in result['answers']}
    assert answers_by_nick['jugador1']['points_awarded'] == 100
    assert answers_by_nick['jugador2']['points_awarded'] == 0


def test_raises_when_no_active_question(lobby_session):
    lobby_session.current_level_index = 2
    lobby_session.save(update_fields=['current_level_index'])

    with pytest.raises(NoActiveQuestion):
        RevealAnswer().execute(lobby_session.id)
