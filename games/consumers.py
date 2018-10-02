import enum
import random
import uuid
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from games.models import Game
from games.serializers import GameSerializer


class MessageType(enum.Enum):
    ACCEPTED = 'accepted'
    REJECTED = 'rejected'
    GAME_STATE = 'game_state'


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
            await self.accept()
            query_params = parse_qs(self.scope['query_string'].decode())
            self.player_id = query_params.get('player_id', [None])[0]

            if self.player_id and self.player_id not in self.game.player_ids.values():
                    self.player_id = None

            if not self.player_id:
                if await self.can_join():
                    self.mark = random.choice([
                        mark for (mark, player_id) in self.game.player_ids.items() if not player_id
                    ])
                    self.player_id = str(uuid.uuid4())
                    await self.add_player()
                    await self.broadcast_game_state()

            serializer = GameSerializer(self.game)
            content = {'game': serializer.data}
            if self.player_id:
                message_type = MessageType.ACCEPTED
                content['game']['player_id'] = self.player_id
            else:
                message_type = MessageType.REJECTED

            await self.send_message(message_type, content)
            await self.channel_layer.group_add(
                self.game_id,
                self.channel_name
            )

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.game_id,
            self.channel_name
        )

    async def receive_json(self, content, **kwargs):
        pass

    async def broadcast(self, message_type, content):
        await self.channel_layer.group_send(
            self.game_id,
            {
                'type': message_type,
                'content': content
            }
        )

    async def send_message(self, message_type: MessageType, content):
        await self.send_json({
            'type': message_type.value,
            'content': content
        })

    async def broadcast_game_state(self):
        serializer = GameSerializer(self.game)
        await self.broadcast('game_state_message', serializer.data)

    async def game_state_message(self, event):
        game_state = event['content']
        await self.send_game_state(game_state)

    async def send_game_state(self, game_state):
        await self.send_message(MessageType.GAME_STATE, {'game': game_state})

    @database_sync_to_async
    def fetch_game(self):
        self.game = Game.objects.filter(id=self.game_id).first()

    @database_sync_to_async
    def add_player(self):
        self.game.player_ids[self.mark] = self.player_id

        if self.game.is_full():
            self.game.first_player = random.choice(list(self.game.player_ids.keys()))

        self.game.save()

    async def can_join(self):
        return not self.game.is_full()
