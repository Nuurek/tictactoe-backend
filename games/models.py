import uuid
from enum import Enum

from django.contrib.postgres.fields import ArrayField, JSONField
from django.db import models

BOARD_SIZE = 9


class Field(Enum):
    O = 'O'
    X = 'X'

    @classmethod
    def choices(cls):
        return [(key, key) for key in cls.__members__.keys()]


def empty_fields():
    return [None for _ in range(BOARD_SIZE)]


def default_player_ids():
    return {
        field.value: None for field in Field
    }


def winner_choices():
    return Field.choices() + [('draw', 'draw')]


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fields = ArrayField(
        models.CharField(null=True, choices=Field.choices(), max_length=1), size=BOARD_SIZE, default=empty_fields
    )
    first_player = models.CharField(null=True, choices=Field.choices(), max_length=1)
    winner = models.CharField(null=True, choices=winner_choices(), max_length=1)
    current_turn = models.CharField(null=True, choices=Field.choices(), max_length=1)
    player_ids = JSONField(default=default_player_ids)

    def is_full(self):
        left_slots = len(self.player_ids) - sum([1 if player_id else 0 for player_id in self.player_ids.values()])
        return left_slots == 0

    @property
    def player_marks(self):
        return {
            player_id: mark for mark, player_id in self.player_ids.items() if player_id
        }
