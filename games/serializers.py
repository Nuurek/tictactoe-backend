from rest_framework import serializers

from games.models import Game


class GameSerializer(serializers.ModelSerializer):
    class Meta:
        model = Game
        fields = ('id', 'fields', 'first_player', 'winner', 'current_turn')
        read_only_fields = ('id', 'fields', 'first_player', 'winner', 'current_turn')
