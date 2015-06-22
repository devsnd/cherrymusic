# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0003_remove_file_date_updated'),
    ]

    operations = [
        migrations.AddField(
            model_name='file',
            name='has_meta',
            field=models.BooleanField(default=False),
        ),
    ]
