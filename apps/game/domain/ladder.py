from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class LadderLevel:
    index: int
    points: int
    is_checkpoint: bool = False


class LadderStrategy(ABC):
    """Estrategia intercambiable para la escalera de premios/puntos de una partida."""

    @abstractmethod
    def total_levels(self) -> int: ...

    @abstractmethod
    def points_for_level(self, level_index: int) -> int: ...

    @abstractmethod
    def is_checkpoint(self, level_index: int) -> bool: ...

    @abstractmethod
    def safe_points_before(self, level_index: int) -> int:
        """Puntos garantizados si el jugador falla en level_index (ultimo checkpoint superado)."""


class FixedLadderStrategy(LadderStrategy):
    """Escalera con niveles y puntos fijos, definidos de antemano (ej. desde un LadderTemplate)."""

    def __init__(self, levels: list[LadderLevel]):
        if not levels:
            raise ValueError('La escalera necesita al menos un nivel')
        self._levels = sorted(levels, key=lambda level: level.index)

    def total_levels(self) -> int:
        return len(self._levels)

    def _level(self, level_index: int) -> LadderLevel:
        try:
            return self._levels[level_index]
        except IndexError:
            raise ValueError(f'Nivel invalido: {level_index}')

    def points_for_level(self, level_index: int) -> int:
        return self._level(level_index).points

    def is_checkpoint(self, level_index: int) -> bool:
        return self._level(level_index).is_checkpoint

    def safe_points_before(self, level_index: int) -> int:
        safe = 0
        for level in self._levels[:level_index]:
            if level.is_checkpoint:
                safe = level.points
        return safe
