from rest_framework import serializers

from .models import Monitor


class MonitorSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    current_status = serializers.SerializerMethodField()

    class Meta:
        model = Monitor
        fields = [
            'id', 'owner', 'name', 'url', 'method',
            'check_interval_seconds', 'timeout_seconds', 'expected_status_code',
            'is_active', 'last_checked_at', 'current_status', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'last_checked_at', 'created_at', 'updated_at']

    def get_current_status(self, monitor):
        # 'up' / 'down' / None (no checks yet) - lets the frontend show a
        # status dot per monitor without fetching each one's check history
        # separately. One extra query per monitor when serializing a list
        # (.first() isn't prefetched) - fine at this scale, worth an
        # annotate/prefetch later if the monitor list ever gets big.
        latest = monitor.checks.order_by('-checked_at').first()
        if latest is None:
            return None
        return 'up' if latest.is_up else 'down'
