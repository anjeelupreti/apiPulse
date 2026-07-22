from django.conf import settings
from django.db import models
from requests.auth import HTTPBasicAuth

from .crypto import decrypt, encrypt


class Monitor(models.Model):
    # This is just the config for what to watch — actual ping results live
    # over in the checks app, not here. Keeping "what to watch" and "what
    # happened" as separate concerns.

    class Method(models.TextChoices):
        GET = 'GET', 'GET'
        POST = 'POST', 'POST'
        HEAD = 'HEAD', 'HEAD'

    class AuthType(models.TextChoices):
        NONE = 'NONE', 'None'
        BASIC = 'BASIC', 'HTTP Basic'
        BEARER = 'BEARER', 'Bearer token'
        API_KEY = 'API_KEY', 'API key header'

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='monitors'
    )
    name = models.CharField(max_length=255)
    url = models.URLField()
    method = models.CharField(max_length=10, choices=Method.choices, default=Method.GET)

    check_interval_seconds = models.PositiveIntegerField(default=60)
    timeout_seconds = models.PositiveIntegerField(default=10)
    expected_status_code = models.PositiveSmallIntegerField(default=200)

    # for a monitor behind auth - see monitors/README.md for why this is
    # encrypted at rest instead of stored as plain text like everything else
    auth_type = models.CharField(max_length=10, choices=AuthType.choices, default=AuthType.NONE)
    auth_header_name = models.CharField(max_length=100, blank=True)  # API_KEY only, e.g. "X-API-Key"
    auth_credential_encrypted = models.TextField(blank=True)

    is_active = models.BooleanField(default=True)
    last_checked_at = models.DateTimeField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def auth_credential(self):
        return decrypt(self.auth_credential_encrypted)

    @auth_credential.setter
    def auth_credential(self, value):
        self.auth_credential_encrypted = encrypt(value)

    def build_auth_kwargs(self):
        """kwargs to splat into requests.request() so a check actually
        authenticates against a protected endpoint. See checks/tasks.py."""
        if self.auth_type == self.AuthType.BASIC:
            username, _, password = self.auth_credential.partition(':')
            return {'auth': HTTPBasicAuth(username, password)}
        if self.auth_type == self.AuthType.BEARER:
            return {'headers': {'Authorization': f'Bearer {self.auth_credential}'}}
        if self.auth_type == self.AuthType.API_KEY:
            header = self.auth_header_name or 'X-API-Key'
            return {'headers': {header: self.auth_credential}}
        return {}
