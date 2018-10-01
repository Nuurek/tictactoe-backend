from django.urls import path

from games.consumers import GameConsumer

urlpatterns = [
    path('<uuid:game_id>', GameConsumer)
]
