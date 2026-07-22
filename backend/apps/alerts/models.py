from django.db import models


class AlertChannel(models.Model):
    # where to send a notification when a monitor's incident opens/resolves.
    # only EMAIL actually sends anything right now — SLACK/WEBHOOK are on
    # the model so I don't have to touch the schema again when I build them

    class ChannelType(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SLACK = 'SLACK', 'Slack'
        WEBHOOK = 'WEBHOOK', 'Webhook'

    monitor = models.ForeignKey(
        'monitors.Monitor', on_delete=models.CASCADE, related_name='alert_channels'
    )
    channel_type = models.CharField(max_length=10, choices=ChannelType.choices)
    # email address for EMAIL, webhook/Slack URL for the other two
    target = models.CharField(max_length=500)
    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.get_channel_type_display()} -> {self.target} ({self.monitor})'


class Notification(models.Model):
    # log of what I actually tried to send, so when someone asks "why didn't
    # I get paged" I have something to look at instead of guessing

    incident = models.ForeignKey(
        'incidents.Incident', on_delete=models.CASCADE, related_name='notifications'
    )
    channel = models.ForeignKey(
        AlertChannel, on_delete=models.CASCADE, related_name='notifications'
    )
    event = models.CharField(max_length=10)  # 'opened' or 'resolved'
    success = models.BooleanField()
    error_message = models.CharField(max_length=500, blank=True)
    sent_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        status = 'ok' if self.success else 'failed'
        return f'{self.event} -> {self.channel.target} ({status})'
