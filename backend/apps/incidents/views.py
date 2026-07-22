from django.utils.dateparse import parse_datetime
from rest_framework import viewsets

from .models import Incident
from .serializers import IncidentSerializer


class IncidentViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = IncidentSerializer

    def get_queryset(self):
        queryset = Incident.objects.filter(monitor__owner=self.request.user)
        params = self.request.query_params

        monitor_id = params.get('monitor')
        if monitor_id is not None:
            queryset = queryset.filter(monitor_id=monitor_id)

        # date range is against started_at - when the outage began, not when
        # it resolved, so "incidents in June" means "started in June"
        since = parse_datetime(params.get('since', '') or '')
        if since is not None:
            queryset = queryset.filter(started_at__gte=since)
        until = parse_datetime(params.get('until', '') or '')
        if until is not None:
            queryset = queryset.filter(started_at__lte=until)

        # ?resolved=true / ?resolved=false - "false" means still ongoing
        resolved = params.get('resolved')
        if resolved is not None:
            if resolved.lower() == 'true':
                queryset = queryset.filter(resolved_at__isnull=False)
            else:
                queryset = queryset.filter(resolved_at__isnull=True)

        return queryset
