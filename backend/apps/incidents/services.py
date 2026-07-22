from django.utils import timezone

from alerts.tasks import notify_incident

from .models import Incident

# picked 3 in a row so a single dropped packet or slow response doesn't
# open an incident by itself — want actual outages, not noise
FAILURE_THRESHOLD = 3


def evaluate_incident(monitor, check):
    # call this right after saving a Check. handles both directions:
    # opening a new incident on the 3rd straight failure, and closing
    # whatever's open the moment a check succeeds again
    ongoing = Incident.objects.filter(monitor=monitor, resolved_at__isnull=True).first()

    if check.is_up:
        if ongoing:
            ongoing.resolved_at = timezone.now()
            ongoing.save(update_fields=['resolved_at'])
            notify_incident.delay(ongoing.id, 'resolved')
        return

    if ongoing:
        return

    recent_checks = list(monitor.checks.order_by('-checked_at')[:FAILURE_THRESHOLD])
    if len(recent_checks) == FAILURE_THRESHOLD and all(not c.is_up for c in recent_checks):
        incident = Incident.objects.create(monitor=monitor, cause=check.failure_reason)
        notify_incident.delay(incident.id, 'opened')
