from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import AdminStatsView, AdminUserViewSet

router = DefaultRouter()
router.register('admin/users', AdminUserViewSet, basename='admin-user')

urlpatterns = [
    path('admin/stats/', AdminStatsView.as_view(), name='admin-stats'),
] + router.urls
