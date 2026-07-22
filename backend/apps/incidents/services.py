from datetime import timedelta

from django.utils import timezone

from alerts.tasks import notify_incident

from .models import Incident

# picked 3 in a row so a single dropped packet or slow response doesn't
# open an incident by itself — want actual outages, not noise
FAILURE_THRESHOLD = 3

# Sentry doesn't email you once and go quiet on a still-broken issue - it
# re-notifies. adapting that: if an incident is still ongoing this long
# after the last notification, send another one instead of staying silent
# until it finally resolves (which could be hours later).
ESCALATION_INTERVAL = timedelta(minutes=15)


def evaluate_incident(monitor, check):
    # call this right after saving a Check. handles three cases: opening a
    # new incident on the 3rd straight failure, closing one the moment a
    # check succeeds again, and re-notifying if one's been ongoing too long
    ongoing = Incident.objects.filter(monitor=monitor, resolved_at__isnull=True).first()

    if check.is_up:
        if ongoing:
            ongoing.resolved_at = timezone.now()
            ongoing.save(update_fields=['resolved_at'])
            notify_incident.delay(ongoing.id, 'resolved')
        return

    if ongoing:
        last_notified = ongoing.last_escalated_at or ongoing.started_at
        if timezone.now() - last_notified >= ESCALATION_INTERVAL:
            ongoing.last_escalated_at = timezone.now()
            ongoing.save(update_fields=['last_escalated_at'])
            notify_incident.delay(ongoing.id, 'escalated')
        return

    recent_checks = list(monitor.checks.order_by('-checked_at')[:FAILURE_THRESHOLD])
    if len(recent_checks) == FAILURE_THRESHOLD and all(not c.is_up for c in recent_checks):
        incident = Incident.objects.create(monitor=monitor, cause=check.failure_reason)
        notify_incident.delay(incident.id, 'opened')
