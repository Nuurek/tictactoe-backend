from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet

from games.models import Game
from games.serializers import GameSerializer


class GameViewSet(
    mixins.CreateModelMixin,
    GenericViewSet
):
    serializer_class = GameSerializer
    queryset = Game.objects.all()
