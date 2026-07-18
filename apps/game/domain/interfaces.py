from typing import Protocol

from .entities import Question
from .lifecycle import SessionStatus


class QuestionRepository(Protocol):
    def get_questions_for_set(self, question_set_id: int) -> list[Question]: ...


class SessionRepository(Protocol):
    def get_status(self, session_id: int) -> SessionStatus: ...

    def save_status(self, session_id: int, status: SessionStatus) -> None: ...

    def get_current_level_index(self, session_id: int) -> int: ...

    def save_current_level_index(self, session_id: int, level_index: int) -> None: ...


class PlayerRepository(Protocol):
    def add_points(self, player_id: int, points: int) -> None: ...

    def get_score(self, player_id: int) -> int: ...
