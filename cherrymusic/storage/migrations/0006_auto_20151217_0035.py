# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0005_auto_20150614_1442'),
    ]

    operations = [
        migrations.AlterField(
            model_name='file',
            name='meta_track',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='meta_track_total',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='file',
            name='meta_year',
            field=models.CharField(max_length=255, null=True, blank=True),
        ),
    ]
