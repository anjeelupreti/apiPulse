from rest_framework import serializers

from .models import Check


class CheckSerializer(serializers.ModelSerializer):
    class Meta:
        model = Check
        fields = [
            'id', 'monitor', 'is_up', 'status_code', 'response_time_ms',
            'failure_reason', 'ssl_valid', 'ssl_expires_at', 'checked_at',
        ]
        read_only_fields = fields
