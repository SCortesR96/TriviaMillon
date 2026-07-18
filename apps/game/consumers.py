import json

from channels.generic.websocket import AsyncWebsocketConsumer


class PingConsumer(AsyncWebsocketConsumer):
    """Consumer de prueba para validar el transporte WebSocket + Redis de punta a punta."""

    async def connect(self):
        await self.accept()

    async def receive(self, text_data):
        data = json.loads(text_data)
        await self.send(text_data=json.dumps({'type': 'pong', 'echo': data}))
