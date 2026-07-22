from rest_framework import viewsets
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import FeatureFlag
from .serializers import FeatureFlagSerializer


class MyFlagsView(APIView):
    """GET /api/flags/mine/ -> {"response-time-chart": true, ...} - every
    flag resolved for whoever's asking. Deliberately doesn't expose who
    else has a flag or the full FeatureFlag rows - just the yes/no this
    user needs to decide what to render."""

    def get(self, request):
        result = {}
        for flag in FeatureFlag.objects.all():
            if flag.is_globally_enabled:
                result[flag.key] = True
            else:
                result[flag.key] = flag.enabled_for_users.filter(pk=request.user.pk).exists()
        return Response(result)


class AdminFeatureFlagViewSet(viewsets.ModelViewSet):
    # staff-only - this is the write surface, /api/flags/mine/ above is
    # the read-only surface every regular user hits
    permission_classes = [IsAdminUser]
    queryset = FeatureFlag.objects.all().order_by('key')
    serializer_class = FeatureFlagSerializer
