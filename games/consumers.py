import uuid

from channels.generic.websocket import AsyncJsonWebsocketConsumer


class GameConsumer(AsyncJsonWebsocketConsumer):
    game_id = None

    async def connect(self):
        self.game_id = str(self.scope['url_route']['kwargs']['game_id'])

        await self.channel_layer.group_add(
            self.game_id,
            self.channel_name
        )

        await self.accept()

        await self.send_json({'player_id': str(uuid.uuid4())})

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )

    async def receive_json(self, content, **kwargs):
        await self.send_to_players('game_message', content)

    async def send_to_players(self, message_type, content):
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type': message_type,
                'content': content
            }
        )

    async def game_message(self, event):
        content = event['content']

        await self.send_json(content)
