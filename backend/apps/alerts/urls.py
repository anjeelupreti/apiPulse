from rest_framework.routers import DefaultRouter

from .views import AlertChannelViewSet, NotificationViewSet

router = DefaultRouter()
router.register('alert-channels', AlertChannelViewSet, basename='alertchannel')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = router.urls
