from django.db import models


class Incident(models.Model):
    # An outage window. Opened when a monitor starts failing, closed
    # automatically the moment it succeeds again — see services.py for
    # the actual open/resolve decision logic, this is just the record of it.

    monitor = models.ForeignKey(
        'monitors.Monitor', on_delete=models.CASCADE, related_name='incidents'
    )

    started_at = models.DateTimeField(auto_now_add=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    cause = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-started_at']

    @property
    def is_ongoing(self):
        return self.resolved_at is None

    def __str__(self):
        state = 'ongoing' if self.is_ongoing else 'resolved'
        return f'Incident({self.monitor}, {state})'
