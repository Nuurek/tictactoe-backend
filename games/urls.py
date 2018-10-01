from rest_framework.routers import SimpleRouter

from games.views import GameViewSet

router = SimpleRouter(trailing_slash=False)
router.register('games', GameViewSet)

urlpatterns = router.urls
