from django.contrib import admin

from .models import Incident


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('monitor', 'started_at', 'resolved_at', 'is_ongoing')
    list_filter = ('resolved_at',)
