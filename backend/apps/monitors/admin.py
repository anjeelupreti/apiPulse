from django.contrib import admin

from .models import Monitor


@admin.register(Monitor)
class MonitorAdmin(admin.ModelAdmin):
    list_display = ('name', 'url', 'method', 'is_active', 'owner', 'check_interval_seconds')
    list_filter = ('is_active', 'method')
    search_fields = ('name', 'url')
