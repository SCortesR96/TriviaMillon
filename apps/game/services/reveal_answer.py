from ..infrastructure.django_repositories import build_engine_for_session
from ..models import GameSession, PlayerAnswer


class NoActiveQuestion(Exception):
    pass


class RevealAnswer:
    """Expone la opcion correcta de la pregunta activa junto con las respuestas de los jugadores."""

    def execute(self, session_id: int) -> dict:
        session = GameSession.objects.get(id=session_id)
        engine = build_engine_for_session(session)

        question = engine.current_question()
        if question is None:
            raise NoActiveQuestion('No hay pregunta activa en esta sala')

        correct_option = next(o for o in question.options if o.is_correct)
        answers = (
            PlayerAnswer.objects
            .filter(question_id=question.id, player__session_id=session_id)
            .select_related('player')
        )
        return {
            'question_id': question.id,
            'correct_option_id': correct_option.id,
            'answers': [
                {
                    'player_id': a.player_id,
                    'nickname': a.player.nickname,
                    'selected_option_id': a.selected_option_id,
                    'points_awarded': a.points_awarded,
                }
                for a in answers
            ],
        }
