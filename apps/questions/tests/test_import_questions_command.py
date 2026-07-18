import pytest
from django.core.management import call_command
from django.core.management.base import CommandError

from apps.questions.models import QuestionSet

pytestmark = pytest.mark.django_db

HEADER = 'id,categoria,nivel,tags,pregunta,opcion_a,opcion_b,opcion_c,opcion_d,respuesta_correcta,explicacion,cita_biblica'


def test_command_imports_file(tmp_path):
    csv_path = tmp_path / 'preguntas.csv'
    csv_path.write_text(
        HEADER + '\n1,Personajes,principiante,fe,Pregunta CLI,A,B,C,D,A,explicacion,ref\n',
        encoding='utf-8',
    )

    call_command('import_questions', str(csv_path), '--set', 'Banco CLI')

    assert QuestionSet.objects.filter(name='Banco CLI').exists()


def test_command_missing_file_raises():
    with pytest.raises(CommandError):
        call_command('import_questions', '/no/existe.csv', '--set', 'Banco CLI')


def test_command_writes_report_file(tmp_path):
    csv_path = tmp_path / 'preguntas.csv'
    csv_path.write_text(
        HEADER + '\n,Personajes,principiante,fe,,A,B,C,D,A,explicacion,ref\n',  # pregunta vacia
        encoding='utf-8',
    )
    report_path = tmp_path / 'reporte.csv'

    call_command('import_questions', str(csv_path), '--set', 'Banco CLI', '--report', str(report_path))

    assert report_path.exists()
    assert 'pregunta vacia' in report_path.read_text(encoding='utf-8')
