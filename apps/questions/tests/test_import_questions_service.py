import io

import pytest
from django.conf import settings

from apps.questions.models import Question, QuestionSet
from apps.questions.services.import_questions import ImportQuestionsFromFile, InvalidImportFile

pytestmark = pytest.mark.django_db

HEADER = 'id,categoria,nivel,tags,pregunta,opcion_a,opcion_b,opcion_c,opcion_d,respuesta_correcta,explicacion,cita_biblica'


def make_csv(rows, filename='preguntas.csv'):
    content = HEADER + '\n' + '\n'.join(rows)
    file = io.BytesIO(content.encode('utf-8'))
    file.name = filename
    return file


def test_creates_question_set_and_questions():
    csv_file = make_csv([
        '1,Personajes,principiante,fe,Quien construyo el arca?,Noe,Abraham,Moises,Job,A,Genesis 6,Genesis 6:14',
    ])

    result = ImportQuestionsFromFile().execute(csv_file, 'Mi banco')

    assert result.created == 1
    assert result.total_rows == 1
    assert result.problems == []
    assert QuestionSet.objects.filter(name='Mi banco').exists()
    question = Question.objects.get(question_set__name='Mi banco')
    assert question.category.name == 'Personajes'
    assert question.difficulty == 'principiante'
    assert question.options.get(is_correct=True).text == 'Noe'


def test_reuses_existing_question_set_by_name():
    QuestionSet.objects.create(name='Mi banco', description='ya existia')
    csv_file = make_csv(['1,Personajes,principiante,fe,Pregunta 1,A,B,C,D,A,explicacion,ref'])

    result = ImportQuestionsFromFile().execute(csv_file, 'Mi banco')

    assert QuestionSet.objects.filter(name='Mi banco').count() == 1
    assert result.question_set.description == 'ya existia'


def test_reimporting_same_ids_skips_duplicates():
    ImportQuestionsFromFile().execute(
        make_csv(['1,Personajes,principiante,fe,Pregunta 1,A,B,C,D,A,explicacion,ref']), 'Mi banco',
    )

    result = ImportQuestionsFromFile().execute(
        make_csv(['1,Personajes,principiante,fe,Pregunta 1,A,B,C,D,A,explicacion,ref']), 'Mi banco',
    )

    assert result.created == 0
    assert len(result.problems) == 1
    assert 'duplicado' in result.problems[0].reason


def test_invalid_rows_are_reported_not_raised():
    csv_file = make_csv([
        ',Personajes,principiante,fe,,A,B,C,D,A,explicacion,ref',  # pregunta vacia
        '2,Personajes,principiante,fe,Pregunta valida,A,B,C,D,Z,explicacion,ref',  # respuesta_correcta invalida
    ])

    result = ImportQuestionsFromFile().execute(csv_file, 'Mi banco')

    assert result.created == 0
    assert len(result.problems) == 2


def test_missing_required_columns_raises():
    file = io.BytesIO(b'id,pregunta\n1,hola')
    file.name = 'malo.csv'

    with pytest.raises(InvalidImportFile):
        ImportQuestionsFromFile().execute(file, 'Mi banco')


def test_unsupported_extension_raises():
    file = io.BytesIO(b'no importa')
    file.name = 'archivo.txt'

    with pytest.raises(InvalidImportFile):
        ImportQuestionsFromFile().execute(file, 'Mi banco')


def test_imports_real_bible_question_bank():
    path = settings.BASE_DIR / 'data' / 'questions' / 'preguntas_biblicas_1000.csv'

    result = ImportQuestionsFromFile().execute(path, 'Preguntas Biblicas (test)')

    assert result.created == 1000
    assert result.problems == []
