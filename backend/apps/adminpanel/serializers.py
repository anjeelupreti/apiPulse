from rest_framework import serializers

from accounts.models import User


class AdminUserSerializer(serializers.ModelSerializer):
    monitor_count = serializers.SerializerMethodField()

    def get_monitor_count(self, user):
        return user.monitors.count()

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'is_active', 'is_staff',
            'date_joined', 'monitor_count',
        ]
        # is_active is the one thing an admin can actually change here -
        # everything else (username, email, is_staff) is view-only from
        # this panel. Promoting someone to staff isn't a button I want to
        # expose casually; that stays a manage.py/Django-admin action.
        read_only_fields = ['id', 'username', 'email', 'is_staff', 'date_joined', 'monitor_count']
