from django.contrib import admin

from .models import Check


@admin.register(Check)
class CheckAdmin(admin.ModelAdmin):
    list_display = ('monitor', 'is_up', 'status_code', 'response_time_ms', 'checked_at')
    list_filter = ('is_up',)
    date_hierarchy = 'checked_at'
