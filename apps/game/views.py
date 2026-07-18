import io
import secrets

import qrcode
from django.http import HttpResponse, HttpResponseNotFound
from django.shortcuts import redirect, render
from django.urls import reverse

from apps.questions.models import QuestionSet

from .models import GameSession, LadderTemplate
from .services.create_session import CreateSession


def _player_join_url(request, code: str) -> str:
    path = reverse('game:player_join')
    return request.build_absolute_uri(f'{path}?code={code}')


def host_new_session(request):
    """Formulario para que el host elija QuestionSet + LadderTemplate y cree una sala."""
    if request.method == 'POST':
        session = CreateSession().execute(
            question_set_id=request.POST['question_set'],
            ladder_template_id=request.POST['ladder_template'],
            host_token=secrets.token_urlsafe(24),
        )
        url = reverse('game:host_session', args=[session.code])
        return redirect(f'{url}?token={session.host_token}')

    return render(request, 'host/new_session.html', {
        'question_sets': QuestionSet.objects.all(),
        'ladder_templates': LadderTemplate.objects.all(),
    })


def host_session(request, code):
    """Pantalla unica del host: sala/pregunta/resultados, todo dirigido por eventos WebSocket."""
    session = GameSession.objects.filter(code=code).first()
    if session is None:
        return HttpResponseNotFound('No existe esa sala')

    return render(request, 'host/session.html', {
        'session': session,
        'code': code,
        'host_token': request.GET.get('token', ''),
        'join_url': _player_join_url(request, code),
    })


def host_qr(request, code):
    """Devuelve un PNG con el QR que apunta a la pantalla de union del jugador."""
    img = qrcode.make(_player_join_url(request, code))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    return HttpResponse(buffer.getvalue(), content_type='image/png')


def player_join(request):
    """Pantalla unica del jugador: unirse, sala de espera, responder y ver resultados."""
    return render(request, 'player/join.html', {'code': request.GET.get('code', '')})
