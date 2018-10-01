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


class Game(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    fields = ArrayField(
        models.CharField(null=True, choices=Field.choices(), max_length=1), size=BOARD_SIZE, default=empty_fields
    )
    first_player = models.CharField(null=True, choices=Field.choices(), max_length=1)
    winner = models.CharField(null=True, choices=Field.choices(), max_length=1)
    current_turn = models.CharField(null=True, choices=Field.choices(), max_length=1)
    player_ids = JSONField(default=default_player_ids)
