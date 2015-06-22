# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0002_auto_20150614_1413'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='date_updated',
        ),
    ]
