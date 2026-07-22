from django.conf import settings
from django.db import models


class Monitor(models.Model):
    """A single API/website endpoint to watch. This is the config; actual
    ping results are stored per-check in the `checks` app, not here."""

    class Method(models.TextChoices):
        GET = 'GET', 'GET'
        POST = 'POST', 'POST'
        HEAD = 'HEAD', 'HEAD'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monitors'
    )
    name = models.CharField(max_length=255)
    url = models.URLField()
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.GET)

    check_interval_seconds = models.PositiveIntegerField(default=60)
    timeout_seconds = models.PositiveIntegerField(default=10)
    expected_status_code = models.PositiveSmallIntegerField(default=200)

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name
