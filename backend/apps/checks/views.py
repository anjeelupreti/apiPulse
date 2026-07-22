from rest_framework import viewsets

from .models import Check
from .serializers import CheckSerializer


class CheckViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CheckSerializer

    def get_queryset(self):
        queryset = Check.objects.filter(monitor__owner=self.request.user)
        monitor_id = self.request.query_params.get('monitor')
        if monitor_id is not None:
            queryset = queryset.filter(monitor_id=monitor_id)
        return queryset
