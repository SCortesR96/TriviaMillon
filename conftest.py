import pytest


@pytest.fixture(autouse=True)
def use_plain_static_storage(settings):
    """Los tests no corren collectstatic; evita depender del manifest de WhiteNoise.

    django.test siempre corre con DEBUG=False (comportamiento documentado de Django),
    y ManifestStaticFilesStorage solo se salta la resolucion por hash cuando DEBUG=True
    (asi es como dev/runserver funciona sin haber corrido collectstatic). Sin este
    fixture, cualquier template que use {% static %} truena en los tests con
    "Missing staticfiles manifest entry" porque el manifest solo existe en la imagen
    de produccion (se genera en el Dockerfile en build time).
    """
    settings.STORAGES = {
        **settings.STORAGES,
        'staticfiles': {'BACKEND': 'django.contrib.staticfiles.storage.StaticFilesStorage'},
    }
