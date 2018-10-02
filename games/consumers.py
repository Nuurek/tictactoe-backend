import random
import uuid
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from games.models import Game


class GameConsumer(AsyncJsonWebsocketConsumer):
    game_id = None
    game: Game = None
    player_id = None
    mark = None

    async def connect(self):
        self.game_id = str(self.scope['url_route']['kwargs']['game_id'])
        await self.fetch_game()

        if not self.game:
            await self.close()
        else:
            query_params = parse_qs(self.scope['query_string'].decode())
            self.player_id = query_params.get('player_id', [None])[0]

            if self.player_id:
                if self.player_id in self.game.player_ids.values():
                    self.mark = list(filter(lambda t: t[1] == self.player_id, self.game.player_ids.items()))[0][0]
                    self.player_id = str(uuid.uuid4())
                else:
                    self.player_id = None

            if not self.player_id:
                if await self.can_join():
                    self.mark = random.choice([
                        mark for (mark, player_id) in self.game.player_ids.items() if not player_id
                    ])
                    self.player_id = str(uuid.uuid4())
                else:
                    await self.close()

            if self.player_id:
                await self.update_player_id()

                await self.channel_layer.group_add(
                    self.game_id,
                    self.channel_name
                )
                await self.accept()

                await self.send_json({'player_id': self.player_id})

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

    @database_sync_to_async
    def fetch_game(self):
        self.game = Game.objects.filter(id=self.game_id).first()

    @database_sync_to_async
    def update_player_id(self):
        self.game.player_ids[self.mark] = self.player_id
        self.game.save()

    async def can_join(self):
        player_ids = self.game.player_ids.values()
        left_slots = len(player_ids) - sum([1 if player_id else 0 for player_id in player_ids])
        return left_slots > 0
