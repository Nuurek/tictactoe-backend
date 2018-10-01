from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.urls import path

from games.routing import urlpatterns as games_urlpatterns

urlpatterns = [
    path('games', URLRouter(games_urlpatterns))
]

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(urlpatterns)
    )
})
