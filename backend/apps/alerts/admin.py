from django.contrib import admin

from .models import AlertChannel, Notification


@admin.register(AlertChannel)
class AlertChannelAdmin(admin.ModelAdmin):
    list_display = ('monitor', 'channel_type', 'target', 'is_active')
    list_filter = ('channel_type', 'is_active')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('channel', 'event', 'success', 'sent_at')
    list_filter = ('event', 'success')
