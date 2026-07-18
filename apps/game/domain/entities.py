from dataclasses import dataclass


@dataclass(frozen=True)
class AnswerOption:
    id: int
    text: str
    is_correct: bool


@dataclass(frozen=True)
class Question:
    id: int
    text: str
    options: list[AnswerOption]
    order: int | None = None

    def option_is_correct(self, option_id: int) -> bool:
        for option in self.options:
            if option.id == option_id:
                return option.is_correct
        raise ValueError(f'La pregunta {self.id} no tiene la opcion {option_id}')
