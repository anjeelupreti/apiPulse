import time

import requests
from celery import shared_task

from incidents.services import evaluate_incident
from monitors.models import Monitor

from .models import Check
from .ssl_check import check_ssl_certificate


@shared_task
def perform_check(monitor_id):
    # this is the actual work: ping it, log a Check either way, then hand
    # off to incidents to decide if that changes anything about an outage
    try:
        monitor = Monitor.objects.get(pk=monitor_id, is_active=True)
    except Monitor.DoesNotExist:
        return None

    is_up = False
    status_code = None
    response_time_ms = None
    failure_reason = ''

    start = time.monotonic()
    try:
        response = requests.request(monitor.method, monitor.url, timeout=monitor.timeout_seconds)
        response_time_ms = int((time.monotonic() - start) * 1000)
        status_code = response.status_code
        is_up = status_code == monitor.expected_status_code
        if not is_up:
            failure_reason = f'Expected status {monitor.expected_status_code}, got {status_code}'
    except requests.exceptions.Timeout:
        failure_reason = 'Request timed out'
    except requests.exceptions.RequestException as exc:
        failure_reason = str(exc)

    # separate TLS handshake from the one `requests` already did above -
    # a bit wasteful (two handshakes per check instead of one) but a lot
    # simpler to reason about than digging the cert out of requests'
    # connection internals. fine at this scale.
    ssl_valid, ssl_expires_at = check_ssl_certificate(monitor.url, timeout=monitor.timeout_seconds)

    check = Check.objects.create(
        monitor=monitor,
        is_up=is_up,
        status_code=status_code,
        response_time_ms=response_time_ms,
        failure_reason=failure_reason,
        ssl_valid=ssl_valid,
        ssl_expires_at=ssl_expires_at,
    )

    monitor.last_checked_at = check.checked_at
    monitor.save(update_fields=['last_checked_at'])

    evaluate_incident(monitor, check)

    return check.id
