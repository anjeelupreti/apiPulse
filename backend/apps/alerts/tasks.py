from celery import shared_task
from django.core.mail import send_mail

from incidents.models import Incident

from .models import AlertChannel, Notification


def _send_email(channel, incident, event):
    subject = f'[PulseWatch] {incident.monitor.name} {event}'
    if event == 'opened':
        body = (
            f'{incident.monitor.name} ({incident.monitor.url}) started failing.\n'
            f'Cause: {incident.cause or "unknown"}\n'
            f'Started at: {incident.started_at}'
        )
    elif event == 'escalated':
        body = (
            f'{incident.monitor.name} ({incident.monitor.url}) is STILL down.\n'
            f'Ongoing since: {incident.started_at}'
        )
    else:  # resolved
        body = (
            f'{incident.monitor.name} ({incident.monitor.url}) recovered.\n'
            f'Resolved at: {incident.resolved_at}'
        )
    send_mail(subject, body, None, [channel.target])


# only email is wired up — Slack/webhook channels get created fine but
# there's nothing here to actually send them yet
SENDERS = {
    AlertChannel.ChannelType.EMAIL: _send_email,
}


@shared_task
def notify_incident(incident_id, event):
    """Fan out one incident event (opened/escalated/resolved) to every
    active AlertChannel on that monitor. Called from
    incidents.services.evaluate_incident."""
    try:
        incident = Incident.objects.get(pk=incident_id)
    except Incident.DoesNotExist:
        return

    channels = AlertChannel.objects.filter(monitor=incident.monitor, is_active=True)
    for channel in channels:
        sender = SENDERS.get(channel.channel_type)
        success = True
        error_message = ''
        if sender is None:
            success = False
            error_message = f'no sender implemented for {channel.channel_type} yet'
        else:
            try:
                sender(channel, incident, event)
            except Exception as exc:
                success = False
                error_message = str(exc)[:500]

        Notification.objects.create(
            incident=incident, channel=channel, event=event,
            success=success, error_message=error_message,
        )
