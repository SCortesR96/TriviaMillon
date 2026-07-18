import os

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = (
        'Crea el superusuario de Django a partir de variables de entorno '
        '(DJANGO_SUPERUSER_USERNAME/EMAIL/PASSWORD) si todavia no existe. '
        'Idempotente: pensado para correr en cada arranque del contenedor en produccion, '
        'donde no hay una terminal interactiva para usar createsuperuser a mano.'
    )

    def handle(self, *args, **options):
        username = os.environ.get('DJANGO_SUPERUSER_USERNAME')
        password = os.environ.get('DJANGO_SUPERUSER_PASSWORD')
        email = os.environ.get('DJANGO_SUPERUSER_EMAIL', '')

        if not username or not password:
            self.stdout.write(
                'DJANGO_SUPERUSER_USERNAME/DJANGO_SUPERUSER_PASSWORD no configurados; '
                'no se crea ningun superusuario.'
            )
            return

        User = get_user_model()
        if User.objects.filter(username=username).exists():
            self.stdout.write(f'El superusuario "{username}" ya existe, no se hace nada.')
            return

        User.objects.create_superuser(username=username, email=email, password=password)
        self.stdout.write(self.style.SUCCESS(f'Superusuario "{username}" creado.'))
