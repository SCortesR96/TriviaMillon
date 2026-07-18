import csv
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from apps.questions.services.import_questions import ImportQuestionsFromFile, InvalidImportFile


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

        try:
            result = ImportQuestionsFromFile().execute(path, options['set_name'], options['set_description'])
        except InvalidImportFile as exc:
            raise CommandError(str(exc))

        self.stdout.write(self.style.SUCCESS(
            f'Importacion completa: {result.created} creadas, {len(result.problems)} omitidas '
            f'(invalidas/duplicadas), {result.total_rows} filas leidas.'
        ))
        if result.problems:
            preview = result.problems[:20]
            self.stdout.write(self.style.WARNING('Primeras filas omitidas:'))
            for p in preview:
                self.stdout.write(f'  fila {p.row} (id={p.source_id}): {p.reason} -- {p.text[:60]}')
            if len(result.problems) > len(preview):
                self.stdout.write(f'  ... y {len(result.problems) - len(preview)} mas.')

        if options['report_path']:
            report_path = Path(options['report_path'])
            with report_path.open('w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=['fila', 'id', 'pregunta', 'motivo'])
                writer.writeheader()
                writer.writerows([
                    {'fila': p.row, 'id': p.source_id, 'pregunta': p.text, 'motivo': p.reason}
                    for p in result.problems
                ])
            self.stdout.write(f'Reporte completo escrito en {report_path}')
