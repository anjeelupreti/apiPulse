from django.db import models


class Check(models.Model):
    """Result of one probe against a Monitor. High write volume, append-only
    (never updated after creation) — the Celery worker inserts one of these
    every time it pings a monitor."""

    monitor = models.ForeignKey(
        'monitors.Monitor', on_delete=models.CASCADE, related_name='checks'
    )

    is_up = models.BooleanField()
    status_code = models.PositiveSmallIntegerField(null=True, blank=True)
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    failure_reason = models.CharField(max_length=255, blank=True)

    ssl_valid = models.BooleanField(null=True, blank=True)
    ssl_expires_at = models.DateTimeField(null=True, blank=True)

    checked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-checked_at']
        indexes = [models.Index(fields=['monitor', '-checked_at'])]

    def __str__(self):
        status = 'up' if self.is_up else 'down'
        return f'{self.monitor} @ {self.checked_at:%Y-%m-%d %H:%M:%S} ({status})'
