from .entities import Question
from .game_mode import ClassicGameModeStrategy, GameModeStrategy
from .ladder import LadderStrategy
from .lifecycle import SessionLifecycleService, SessionStatus
from .scoring import ScoringService
from .selection import QuestionSelectionService


class GameEngine:
    """Orquesta ladder, seleccion de preguntas, scoring y ciclo de vida de una partida.

    Dominio puro: no conoce Django, WebSockets ni persistencia. Los use cases
    (services/) lo alimentan con datos leidos via los repositorios y persisten
    el resultado (puntajes, estado de la sesion, etc).
    """

    def __init__(
        self,
        questions: list[Question],
        ladder: LadderStrategy,
        game_mode: GameModeStrategy | None = None,
    ):
        self._selection = QuestionSelectionService(questions)
        self._scoring = ScoringService(ladder)
        self._game_mode = game_mode or ClassicGameModeStrategy()
        self._lifecycle = SessionLifecycleService()
        self.status = SessionStatus.LOBBY
        self.current_level_index = 0

    def start(self) -> None:
        self.status = self._lifecycle.transition(self.status, SessionStatus.IN_PROGRESS)

    def current_question(self) -> Question | None:
        return self._selection.question_at(self.current_level_index)

    def submit_answer(self, option_id: int) -> int:
        question = self.current_question()
        if question is None:
            raise ValueError('No hay pregunta activa')
        is_correct = question.option_is_correct(option_id)
        return self._scoring.score_for_answer(self.current_level_index, is_correct)

    def advance(self) -> Question | None:
        self.current_level_index += 1
        if self.is_over():
            self.status = self._lifecycle.transition(self.status, SessionStatus.FINISHED)
            return None
        return self.current_question()

    def is_over(self) -> bool:
        return self._game_mode.is_game_over(self.current_level_index, self._selection.total_questions())
