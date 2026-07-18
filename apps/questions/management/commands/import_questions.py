import csv
from pathlib import Path

import pandas as pd
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.questions.models import AnswerOption, Category, Question, QuestionSet

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


class Command(BaseCommand):
    help = 'Importa preguntas desde un archivo CSV/Excel a un QuestionSet.'

    def add_arguments(self, parser):
        parser.add_argument('file', type=str, help='Ruta al archivo .csv/.xlsx con las preguntas')
        parser.add_argument('--set', dest='set_name', required=True, help='Nombre del QuestionSet destino')
        parser.add_argument('--set-description', dest='set_description', default='', help='Descripcion del QuestionSet (solo al crearlo)')
        parser.add_argument('--report', dest='report_path', default='', help='Ruta opcional para volcar un CSV con filas invalidas/duplicadas')

    def handle(self, *args, **options):
        path = Path(options['file'])
        if not path.exists():
            raise CommandError(f'No existe el archivo: {path}')

        if path.suffix.lower() in ('.xlsx', '.xls'):
            df = pd.read_excel(path, dtype=str)
        elif path.suffix.lower() == '.csv':
            df = pd.read_csv(path, dtype=str)
        else:
            raise CommandError(f'Extension no soportada: {path.suffix} (usa .csv o .xlsx)')

        missing_columns = [c for c in REQUIRED_COLUMNS if c not in df.columns]
        if missing_columns:
            raise CommandError(f'Faltan columnas requeridas en el archivo: {missing_columns}')

        question_set, _ = QuestionSet.objects.get_or_create(
            name=options['set_name'],
            defaults={'description': options['set_description']},
        )

        categories_cache = {c.name: c for c in Category.objects.all()}
        seen_source_ids = set()
        existing_source_ids = set(
            question_set.questions.exclude(source_id='').values_list('source_id', flat=True)
        )

        created = 0
        problems = []  # list of dicts: row, source_id, pregunta, motivo

        with transaction.atomic():
            for i, row in df.iterrows():
                row_num = i + 2  # +2: header row + 1-indexed
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
                    problems.append({
                        'fila': row_num, 'id': source_id, 'pregunta': text, 'motivo': reason,
                    })
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

        self.stdout.write(self.style.SUCCESS(
            f'Importacion completa: {created} creadas, {len(problems)} omitidas '
            f'(invalidas/duplicadas), {len(df)} filas leidas.'
        ))
        if problems:
            preview = problems[:20]
            self.stdout.write(self.style.WARNING('Primeras filas omitidas:'))
            for p in preview:
                self.stdout.write(f"  fila {p['fila']} (id={p['id']}): {p['motivo']} -- {p['pregunta'][:60]}")
            if len(problems) > len(preview):
                self.stdout.write(f'  ... y {len(problems) - len(preview)} mas.')

        if options['report_path']:
            report_path = Path(options['report_path'])
            with report_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['fila', 'id', 'pregunta', 'motivo'])
                writer.writeheader()
                writer.writerows(problems)
            self.stdout.write(f'Reporte completo escrito en {report_path}')
