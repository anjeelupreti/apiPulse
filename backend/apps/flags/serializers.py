from rest_framework import serializers

from .models import FeatureFlag


class FeatureFlagSerializer(serializers.ModelSerializer):
    # staff-only CRUD (see AdminFeatureFlagViewSet) - not the same endpoint
    # a regular user hits, so it's fine for this to be a heavier, fuller
    # representation than /api/flags/mine/'s plain {key: bool} map
    class Meta:
        model = FeatureFlag
        fields = [
            'id', 'key', 'description', 'is_globally_enabled', 'enabled_for_users',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
