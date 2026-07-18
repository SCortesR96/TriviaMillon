from django.urls import re_path

from apps.game.consumers import GameConsumer, PingConsumer

websocket_urlpatterns = [
    re_path(r'^ws/ping/$', PingConsumer.as_asgi()),
    re_path(r'^ws/game/$', GameConsumer.as_asgi()),
]
