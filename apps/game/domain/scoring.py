from .ladder import LadderStrategy


class ScoringService:
    """Unica responsabilidad: calcular los puntos que obtiene un jugador al responder."""

    def __init__(self, ladder: LadderStrategy):
        self._ladder = ladder

    def score_for_answer(self, level_index: int, is_correct: bool) -> int:
        if is_correct:
            return self._ladder.points_for_level(level_index)
        return self._ladder.safe_points_before(level_index)
