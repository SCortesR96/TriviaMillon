from django.db import IntegrityError
from django.db.models import F

from ..infrastructure.django_repositories import build_engine_for_session
from ..models import GameSession, Player, PlayerAnswer


class NoActiveQuestion(Exception):
    pass


class AlreadyAnswered(Exception):
    pass


class SessionPaused(Exception):
    pass


class SubmitAnswer:
    """Registra la respuesta de un jugador a la pregunta activa y le acredita los puntos."""

    def execute(
        self,
        session_id: int,
        player_id: int,
        option_id: int,
        response_time_ms: int | None = None,
    ) -> PlayerAnswer:
        session = GameSession.objects.get(id=session_id)
        if session.is_paused:
            raise SessionPaused('El host puso la partida en pausa')

        engine = build_engine_for_session(session)

        question = engine.current_question()
        if question is None:
            raise NoActiveQuestion('No hay pregunta activa en esta sala')

        points = engine.submit_answer(option_id)

        try:
            answer = PlayerAnswer.objects.create(
                player_id=player_id,
                question_id=question.id,
                selected_option_id=option_id,
                response_time_ms=response_time_ms,
                points_awarded=points,
            )
        except IntegrityError:
            raise AlreadyAnswered('Este jugador ya respondio esta pregunta')

        Player.objects.filter(id=player_id).update(score=F('score') + points)
        return answer
