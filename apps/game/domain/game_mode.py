from abc import ABC, abstractmethod


class GameModeStrategy(ABC):
    """Estrategia intercambiable para las condiciones de fin de partida."""

    @abstractmethod
    def is_game_over(self, current_level_index: int, total_levels: int) -> bool: ...


class ClassicGameModeStrategy(GameModeStrategy):
    """Modo tipo Kahoot: todos los jugadores responden todas las preguntas, sin eliminacion."""

    def is_game_over(self, current_level_index: int, total_levels: int) -> bool:
        return current_level_index >= total_levels
