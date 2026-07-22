from django.utils.dateparse import parse_datetime
from rest_framework import viewsets

from .models import Check
from .serializers import CheckSerializer


class CheckViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = CheckSerializer

    def get_queryset(self):
        queryset = Check.objects.filter(monitor__owner=self.request.user)
        params = self.request.query_params

        monitor_id = params.get('monitor')
        if monitor_id is not None:
            queryset = queryset.filter(monitor_id=monitor_id)

        # ?since=2026-07-01T00:00:00Z&until=2026-07-22T00:00:00Z - both optional,
        # can be used alone (just a lower or upper bound) or together (a range)
        since = parse_datetime(params.get('since', '') or '')
        if since is not None:
            queryset = queryset.filter(checked_at__gte=since)
        until = parse_datetime(params.get('until', '') or '')
        if until is not None:
            queryset = queryset.filter(checked_at__lte=until)

        # ?is_up=true / ?is_up=false - so the frontend can show "failures only"
        is_up = params.get('is_up')
        if is_up is not None:
            queryset = queryset.filter(is_up=is_up.lower() == 'true')

        return queryset
