from dataclasses import dataclass, field
from pathlib import Path

import pandas as pd
from django.db import transaction

from ..models import AnswerOption, Category, Question, QuestionSet

REQUIRED_COLUMNS = [
    'id', 'categoria', 'nivel', 'tags', 'pregunta',
    'opcion_a', 'opcion_b', 'opcion_c', 'opcion_d',
    'respuesta_correcta', 'explicacion', 'cita_biblica',
]
VALID_DIFFICULTIES = {choice for choice, _ in Question.Difficulty.choices}
OPTION_COLUMNS = ['opcion_a', 'opcion_b', 'opcion_c', 'opcion_d']
LETTER_TO_INDEX = {'A': 0, 'B': 1, 'C': 2, 'D': 3}


def clean(value):
    if pd.isna(value):
        return ''
    return str(value).strip()


class InvalidImportFile(Exception):
    pass


@dataclass
class ImportProblem:
    row: int
    source_id: str
    text: str
    reason: str


@dataclass
class ImportResult:
    question_set: QuestionSet
    created: int
    total_rows: int
    problems: list[ImportProblem] = field(default_factory=list)


class ImportQuestionsFromFile:
    """Importa preguntas desde un CSV/Excel a un QuestionSet (lo crea si no existe).

    Usado tanto por el management command (import_questions) como por la vista
    de admin que permite subir el archivo desde el navegador: la logica de
    parseo/validacion vive una sola vez aqui.
    """

    def execute(self, file, set_name: str, set_description: str = '') -> ImportResult:
        df = self._read_dataframe(file)

        missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing_columns:
            raise InvalidImportFile(f'Faltan columnas requeridas en el archivo: {missing_columns}')

        question_set, _ = QuestionSet.objects.get_or_create(
            name=set_name,
            defaults={'description': set_description},
        )

        categories_cache = {c.name: c for c in Category.objects.all()}
        seen_source_ids = set()
        existing_source_ids = set(
            question_set.questions.exclude(source_id='').values_list('source_id', flat=True)
        )

        created = 0
        problems = []

        with transaction.atomic():
            for i, row in df.iterrows():
                row_num = i + 2  # +2: fila de encabezado + 1-indexado
                source_id = clean(row['id'])
                text = clean(row['pregunta'])
                options_text = [clean(row[col]) for col in OPTION_COLUMNS]
                correct_letter = clean(row['respuesta_correcta']).upper()
                difficulty = clean(row['nivel']).lower()
                category_name = clean(row['categoria'])

                reason = None
                if not text:
                    reason = 'pregunta vacia'
                elif sum(1 for o in options_text if o) < 2:
                    reason = 'menos de 2 opciones de respuesta'
                elif correct_letter not in LETTER_TO_INDEX:
                    reason = f'respuesta_correcta invalida: {correct_letter!r}'
                elif not options_text[LETTER_TO_INDEX[correct_letter]]:
                    reason = 'la opcion marcada como correcta esta vacia'
                elif difficulty not in VALID_DIFFICULTIES:
                    reason = f'nivel invalido: {difficulty!r}'
                elif source_id and (source_id in seen_source_ids or source_id in existing_source_ids):
                    reason = f'id duplicado: {source_id!r}'

                if reason:
                    problems.append(ImportProblem(row=row_num, source_id=source_id, text=text, reason=reason))
                    continue

                if source_id:
                    seen_source_ids.add(source_id)

                category = None
                if category_name:
                    category = categories_cache.get(category_name)
                    if category is None:
                        category = Category.objects.create(name=category_name)
                        categories_cache[category_name] = category

                question = Question.objects.create(
                    question_set=question_set,
                    category=category,
                    text=text,
                    difficulty=difficulty,
                    tags=clean(row['tags']),
                    explanation=clean(row['explicacion']),
                    reference=clean(row['cita_biblica']),
                    source_id=source_id,
                )
                AnswerOption.objects.bulk_create([
                    AnswerOption(
                        question=question,
                        text=options_text[idx],
                        is_correct=(idx == LETTER_TO_INDEX[correct_letter]),
                        order=idx,
                    )
                    for idx in range(4) if options_text[idx]
                ])
                created += 1

        return ImportResult(question_set=question_set, created=created, total_rows=len(df), problems=problems)

    def _read_dataframe(self, file):
        name = getattr(file, 'name', str(file))
        suffix = Path(name).suffix.lower()
        if suffix in ('.xlsx', '.xls'):
            return pd.read_excel(file, dtype=str)
        if suffix == '.csv':
            return pd.read_csv(file, dtype=str)
        raise InvalidImportFile(f'Extension no soportada: {suffix!r} (usa .csv o .xlsx)')
