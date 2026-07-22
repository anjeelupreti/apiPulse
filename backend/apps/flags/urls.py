from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AdminFeatureFlagViewSet, MyFlagsView

router = DefaultRouter()
router.register('admin/flags', AdminFeatureFlagViewSet, basename='admin-flag')

urlpatterns = [
    path('flags/mine/', MyFlagsView.as_view(), name='my-flags'),
] + router.urls
