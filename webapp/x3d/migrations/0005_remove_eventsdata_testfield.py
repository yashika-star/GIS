# Generated by Django 4.2.4 on 2024-01-23 13:24

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('x3d', '0004_eventsdata_testfield'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='eventsdata',
            name='testField',
        ),
    ]
