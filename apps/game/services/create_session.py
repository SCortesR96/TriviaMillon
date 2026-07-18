import random
import string

from ..models import GameSession

_CODE_ALPHABET = string.ascii_uppercase + string.digits
_CODE_LENGTH = 6
_MAX_ATTEMPTS = 10


class CreateSession:
    """Crea una partida en estado lobby para un QuestionSet y LadderTemplate dados."""

    def execute(self, question_set_id: int, ladder_template_id: int, host_token: str) -> GameSession:
        code = self._generate_unique_code()
        return GameSession.objects.create(
            code=code,
            host_token=host_token,
            question_set_id=question_set_id,
            ladder_template_id=ladder_template_id,
        )

    def _generate_unique_code(self) -> str:
        for _ in range(_MAX_ATTEMPTS):
            code = ''.join(random.choices(_CODE_ALPHABET, k=_CODE_LENGTH))
            if not GameSession.objects.filter(code=code).exists():
                return code
        raise RuntimeError('No se pudo generar un codigo de sala unico')
