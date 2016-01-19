# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.contrib.postgres.operations import UnaccentExtension


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_auto_20160111_1715'),
    ]

    operations = [
        UnaccentExtension(),
    ]
