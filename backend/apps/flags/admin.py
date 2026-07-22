from django.contrib import admin

from .models import FeatureFlag


@admin.register(FeatureFlag)
class FeatureFlagAdmin(admin.ModelAdmin):
    list_display = ('key', 'description', 'is_globally_enabled')
    list_filter = ('is_globally_enabled',)
    filter_horizontal = ('enabled_for_users',)
