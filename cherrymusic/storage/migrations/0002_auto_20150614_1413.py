# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('storage', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directory',
            name='parent',
            field=models.ForeignKey(to='storage.Directory', null=True),
        ),
    ]
