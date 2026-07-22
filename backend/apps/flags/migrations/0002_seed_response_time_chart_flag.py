from django.db import migrations


def create_flag(apps, schema_editor):
    FeatureFlag = apps.get_model('flags', 'FeatureFlag')
    FeatureFlag.objects.get_or_create(
        key='response-time-chart',
        defaults={
            'description': 'Show the response-time chart on the monitor detail page',
            'is_globally_enabled': True,
        },
    )


def remove_flag(apps, schema_editor):
    FeatureFlag = apps.get_model('flags', 'FeatureFlag')
    FeatureFlag.objects.filter(key='response-time-chart').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('flags', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(create_flag, remove_flag),
    ]
