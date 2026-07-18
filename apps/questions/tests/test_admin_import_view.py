import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from apps.questions.models import QuestionSet

pytestmark = pytest.mark.django_db

HEADER = 'id,categoria,nivel,tags,pregunta,opcion_a,opcion_b,opcion_c,opcion_d,respuesta_correcta,explicacion,cita_biblica'


@pytest.fixture
def admin_client_logged_in(client, django_user_model):
    admin = django_user_model.objects.create_superuser('admin', 'admin@example.com', 'password123')
    client.force_login(admin)
    return client


def test_import_page_requires_login(client):
    response = client.get(reverse('admin:questions_questionset_import_csv'))

    assert response.status_code == 302


def test_import_page_renders(admin_client_logged_in):
    response = admin_client_logged_in.get(reverse('admin:questions_questionset_import_csv'))

    assert response.status_code == 200
    assert b'form' in response.content


def test_uploading_csv_creates_question_set(admin_client_logged_in):
    content = (HEADER + '\n1,Personajes,principiante,fe,Pregunta admin,A,B,C,D,A,explicacion,ref\n').encode('utf-8')
    upload = SimpleUploadedFile('preguntas.csv', content, content_type='text/csv')

    response = admin_client_logged_in.post(reverse('admin:questions_questionset_import_csv'), {
        'question_set_name': 'Banco desde admin',
        'question_set_description': 'Subido por el host',
        'file': upload,
    })

    assert response.status_code == 302
    question_set = QuestionSet.objects.get(name='Banco desde admin')
    assert question_set.description == 'Subido por el host'
    assert question_set.questions.count() == 1


def test_rejects_file_with_wrong_extension(admin_client_logged_in):
    upload = SimpleUploadedFile('preguntas.txt', b'no importa', content_type='text/plain')

    response = admin_client_logged_in.post(reverse('admin:questions_questionset_import_csv'), {
        'question_set_name': 'Banco malo',
        'file': upload,
    })

    assert response.status_code == 200  # se queda en el formulario mostrando el error
    assert not QuestionSet.objects.filter(name='Banco malo').exists()
