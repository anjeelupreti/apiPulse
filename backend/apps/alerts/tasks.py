import requests
from celery import shared_task
from django.core.mail import send_mail

from incidents.models import Incident

from .models import AlertChannel, Notification


def _message(incident, event):
    # shared by email + Slack, since both want the same "what happened"
    # prose - webhook gets structured JSON instead, different audience
    # (a script reading this, not a person)
    if event == 'opened':
        return (
            f'{incident.monitor.name} started failing',
            f'{incident.monitor.name} ({incident.monitor.url}) started failing.\n'
            f'Cause: {incident.cause or "unknown"}\n'
            f'Started at: {incident.started_at}',
        )
    elif event == 'escalated':
        return (
            f'{incident.monitor.name} still down',
            f'{incident.monitor.name} ({incident.monitor.url}) is STILL down.\n'
            f'Ongoing since: {incident.started_at}',
        )
    else:  # resolved
        return (
            f'{incident.monitor.name} recovered',
            f'{incident.monitor.name} ({incident.monitor.url}) recovered.\n'
            f'Resolved at: {incident.resolved_at}',
        )


def _send_email(channel, incident, event):
    subject, body = _message(incident, event)
    send_mail(f'[PulseWatch] {subject}', body, None, [channel.target])


def _send_slack(channel, incident, event):
    # Slack incoming webhooks: POST {"text": "..."} to the URL Slack gave
    # the user when they set up the webhook (channel.target)
    subject, body = _message(incident, event)
    response = requests.post(channel.target, json={'text': f'*{subject}*\n{body}'}, timeout=5)
    response.raise_for_status()


def _send_webhook(channel, incident, event):
    # generic webhook: structured JSON, not prose - whatever's on the
    # other end (a script, Zapier, PagerDuty's generic webhook) is meant
    # to parse this, not read it
    payload = {
        'event': event,
        'monitor': {
            'id': incident.monitor.id,
            'name': incident.monitor.name,
            'url': incident.monitor.url,
        },
        'incident': {
            'id': incident.id,
            'cause': incident.cause,
            'started_at': incident.started_at.isoformat(),
            'resolved_at': incident.resolved_at.isoformat() if incident.resolved_at else None,
        },
    }
    response = requests.post(channel.target, json=payload, timeout=5)
    response.raise_for_status()


SENDERS = {
    AlertChannel.ChannelType.EMAIL: _send_email,
    AlertChannel.ChannelType.SLACK: _send_slack,
    AlertChannel.ChannelType.WEBHOOK: _send_webhook,
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
