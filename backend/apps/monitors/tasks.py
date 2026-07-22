from datetime import timedelta

from celery import shared_task
from django.utils import timezone

from checks.tasks import perform_check

from .models import Monitor


@shared_task
def dispatch_due_checks():
    # celery beat fires this every 15s (see CELERY_BEAT_SCHEDULE). it doesn't
    # ping anything itself — just figures out who's overdue and queues them
    now = timezone.now()
    for monitor in Monitor.objects.filter(is_active=True):
        interval = timedelta(seconds=monitor.check_interval_seconds)
        if monitor.last_checked_at is None or now - monitor.last_checked_at >= interval:
            perform_check.delay(monitor.id)
