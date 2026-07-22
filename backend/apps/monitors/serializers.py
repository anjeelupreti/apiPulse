from rest_framework import serializers

from .models import Monitor


class MonitorSerializer(serializers.ModelSerializer):
    owner = serializers.PrimaryKeyRelatedField(read_only=True)
    current_status = serializers.SerializerMethodField()
    has_auth_credential = serializers.SerializerMethodField()
    # write-only: the whole point of encrypting this at rest is that it
    # never comes back out through the API either. has_auth_credential
    # (below) is how the frontend shows "a credential is set" without ever
    # seeing the value.
    auth_credential = serializers.CharField(
        write_only=True, required=False, allow_blank=True, style={'input_type': 'password'}
    )

    class Meta:
        model = Monitor
        fields = [
            'id', 'owner', 'name', 'url', 'method',
            'check_interval_seconds', 'timeout_seconds', 'expected_status_code',
            'auth_type', 'auth_header_name', 'auth_credential', 'has_auth_credential',
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

    def get_has_auth_credential(self, monitor):
        return bool(monitor.auth_credential_encrypted)

    def create(self, validated_data):
        credential = validated_data.pop('auth_credential', '')
        monitor = Monitor(**validated_data)
        monitor.auth_credential = credential
        monitor.save()
        return monitor

    def update(self, instance, validated_data):
        # absent entirely (PATCH didn't send it) -> leave the stored
        # credential alone. Present, even as '' -> that's an explicit
        # "clear it" or "set it to this".
        credential = validated_data.pop('auth_credential', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if credential is not None:
            instance.auth_credential = credential
        instance.save()
        return instance
