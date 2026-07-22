from rest_framework import viewsets

from .models import AlertChannel, Notification
from .serializers import AlertChannelSerializer, NotificationSerializer


class AlertChannelViewSet(viewsets.ModelViewSet):
    serializer_class = AlertChannelSerializer

    def get_queryset(self):
        queryset = AlertChannel.objects.filter(monitor__owner=self.request.user)
        monitor_id = self.request.query_params.get('monitor')
        if monitor_id is not None:
            queryset = queryset.filter(monitor_id=monitor_id)
        return queryset


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer

    def get_queryset(self):
        queryset = Notification.objects.filter(channel__monitor__owner=self.request.user)
        monitor_id = self.request.query_params.get('monitor')
        if monitor_id is not None:
            queryset = queryset.filter(channel__monitor_id=monitor_id)
        return queryset
