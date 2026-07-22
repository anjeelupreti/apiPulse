from rest_framework import serializers

from .models import Monitor


class MonitorSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Monitor
        fields = [
            'id', 'owner', 'name', 'url', 'method',
            'check_interval_seconds', 'timeout_seconds', 'expected_status_code',
            'is_active', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
