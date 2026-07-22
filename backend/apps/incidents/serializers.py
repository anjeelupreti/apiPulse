from rest_framework import serializers

from .models import Incident


class IncidentSerializer(serializers.ModelSerializer):
    is_ongoing = serializers.BooleanField(read_only=True)

    class Meta:
        model = Incident
        fields = ['id', 'monitor', 'started_at', 'resolved_at', 'cause', 'is_ongoing']
        read_only_fields = fields
