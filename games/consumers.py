import random
import uuid

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from games.models import Game


class GameConsumer(AsyncJsonWebsocketConsumer):
    game_id = None
    game: Game = None

    async def connect(self):
        self.game_id = str(self.scope['url_route']['kwargs']['game_id'])

        await self.channel_layer.group_add(
            self.game_id,
            self.channel_name
        )

        self.fetch_game()
        if self.can_join():
            await self.accept()

            player_id = self.accept_player()
            await self.send_json({'player_id': player_id})
        else:
            await self.close()

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

    def accept_player(self):
        player_ids = self.game.player_ids
        mark = random.choice([mark for (mark, player_id) in player_ids.items() if not player_id])
        player_id = str(uuid.uuid4())
        self.game.player_ids = {
            **player_ids,
            mark: player_id
        }
        self.game.save()

        return player_id

    def fetch_game(self):
        self.game = Game.objects.filter(id=self.game_id).first()

    def can_join(self):
        player_ids = self.game.player_ids
        left_slots = len(player_ids) - sum([1 if player_id else 0 for player_id in player_ids.values()])

        return self.game and left_slots > 0
