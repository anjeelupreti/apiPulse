from rest_framework import serializers

from .models import AlertChannel, Notification


class AlertChannelSerializer(serializers.ModelSerializer):
    class Meta:
        model = AlertChannel
        fields = ['id', 'monitor', 'channel_type', 'target', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_monitor(self, monitor):
        # can't let someone attach a channel to a monitor they don't own,
        # even though the queryset already hides other people's monitors
        request = self.context['request']
        if monitor.owner_id != request.user.id:
            raise serializers.ValidationError("That's not your monitor.")
        return monitor


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'incident', 'channel', 'event', 'success', 'error_message', 'sent_at']
        read_only_fields = fields
