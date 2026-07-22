from rest_framework import mixins, viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.models import User
from flags.models import FeatureFlag
from incidents.models import Incident
from monitors.models import Monitor

from .serializers import AdminUserSerializer


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        return Response({
            'total_users': User.objects.count(),
            'total_monitors': Monitor.objects.count(),
            'total_ongoing_incidents': Incident.objects.filter(resolved_at__isnull=True).count(),
            'total_feature_flags': FeatureFlag.objects.count(),
        })


class AdminUserViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, mixins.UpdateModelMixin,
    viewsets.GenericViewSet,
):
    # deliberately no create/destroy here - this panel manages existing
    # accounts (mainly: deactivate one), it doesn't create or delete users
    permission_classes = [IsAdminUser]
    queryset = User.objects.all().order_by('-date_joined')
    serializer_class = AdminUserSerializer
