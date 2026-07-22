from rest_framework import viewsets

from .models import Incident
from .serializers import IncidentSerializer


class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IncidentSerializer

    def get_queryset(self):
        queryset = Incident.objects.filter(monitor__owner=self.request.user)
        monitor_id = self.request.query_params.get('monitor')
        if monitor_id is not None:
            queryset = queryset.filter(monitor_id=monitor_id)
        return queryset
