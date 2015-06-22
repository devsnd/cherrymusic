# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0004_file_has_meta'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='file',
            name='has_meta',
        ),
        migrations.AddField(
            model_name='file',
            name='meta_index_date',
            field=models.DateField(null=True, blank=True),
        ),
    ]
