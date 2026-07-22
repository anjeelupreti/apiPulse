from django.conf import settings
from django.db import models


class FeatureFlag(models.Model):
    # generic on purpose - didn't want to hardcode a Python enum of every
    # feature I might ever want to gate. `key` is just a string both sides
    # (backend and frontend) agree on, like an event name.
    key = models.SlugField(unique=True)
    description = models.CharField(max_length=255, blank=True)

    is_globally_enabled = models.BooleanField(default=False)
    # per-user override when NOT globally enabled - lets me turn something
    # on for myself/a beta group without flipping it for everyone
    enabled_for_users = models.ManyToManyField(
        settings.AUTH_USER_MODEL, blank=True, related_name='enabled_flags'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.key


def is_enabled(key, user=None):
    """The one function everything else should call - never query
    FeatureFlag directly elsewhere. Unknown key -> False (fail closed);
    a flag that doesn't exist yet is not a flag that's on."""
    try:
        flag = FeatureFlag.objects.get(key=key)
    except FeatureFlag.DoesNotExist:
        return False

    if flag.is_globally_enabled:
        return True
    if user is not None and getattr(user, 'is_authenticated', False):
        return flag.enabled_for_users.filter(pk=user.pk).exists()
    return False
