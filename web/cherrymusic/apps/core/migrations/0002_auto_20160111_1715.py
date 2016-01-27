# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import cherrymusic.apps.core.models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.AlterModelManagers(
            name='user',
            managers=[
                ('objects', cherrymusic.apps.core.models.UserManagerCaseInsensitive()),
            ],
        ),
        migrations.RemoveField(
            model_name='usersettings',
            name='hotkeys',
        ),
        migrations.RemoveField(
            model_name='usersettings',
            name='misc',
        ),
        migrations.AddField(
            model_name='hotkeyssettings',
            name='user_settings',
            field=models.OneToOneField(to='core.UserSettings', default=1),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='miscsettings',
            name='user_settings',
            field=models.OneToOneField(to='core.UserSettings', default=1),
            preserve_default=False,
        ),
    ]
