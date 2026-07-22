from rest_framework.routers import DefaultRouter

from .views import CheckViewSet

router = DefaultRouter()
router.register('checks', CheckViewSet, basename='check')

urlpatterns = router.urls
