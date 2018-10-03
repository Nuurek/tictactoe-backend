import enum
import random
import uuid
from urllib.parse import parse_qs

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncJsonWebsocketConsumer

from games.models import Game, Field
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
                self.mark = self.game.player_marks[self.player_id]
                content['game']['player_mark'] = self.mark
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
        field = content['field']
        if await self.make_move(field):
            await self.broadcast_game_state()

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
            self.game.current_turn = self.game.first_player

        self.game.save()

    async def can_join(self):
        return not self.game.is_full()

    @database_sync_to_async
    def make_move(self, field):
        self.game.refresh_from_db()

        if self.game.current_turn == self.mark and not self.game.fields[field]:
            self.game.fields[field] = self.mark

            fields = self.game.fields
            rows = [fields[row*3:row*3+3] for row in range(3)]
            columns = [fields[column::3] for column in range(3)]
            axis_one = [[fields[0], fields[4], fields[8]]]
            axis_two = [[fields[2], fields[4], fields[6]]]
            winning_fields = rows + columns + axis_one + axis_two

            is_x_winning = self.check_winning(Field.X.value, winning_fields)
            is_o_winning = self.check_winning(Field.O.value, winning_fields)
            is_draw = all([
                (
                    any([field == Field.X.value for field in fields])
                    and
                    any([field == Field.O.value for field in fields])
                ) for fields in winning_fields
            ])

            if is_x_winning:
                self.game.winner = Field.X.value
            elif is_o_winning:
                self.game.winner = Field.O.value
            elif is_draw:
                self.game.winner = 'draw'

            if self.game.winner:
                self.game.current_turn = None
            else:
                self.game.current_turn = Field.X.value if self.mark == Field.O.value else Field.O.value

            self.game.save()
            return True
        else:
            return False

    @staticmethod
    def check_winning(mark, winning_field):
        return any([
            all([
                field == mark for field in fields
            ]) for fields in winning_field
        ])
