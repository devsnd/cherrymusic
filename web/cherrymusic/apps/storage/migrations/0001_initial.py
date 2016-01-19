# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('path', models.CharField(max_length=255)),
                ('parent', models.ForeignKey(null=True, to='storage.Directory')),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('filename', models.CharField(max_length=255)),
                ('meta_index_date', models.DateField(null=True, blank=True)),
                ('meta_track', models.CharField(max_length=255, null=True, blank=True)),
                ('meta_track_total', models.CharField(max_length=255, null=True, blank=True)),
                ('meta_title', models.CharField(max_length=255, null=True, blank=True)),
                ('meta_artist', models.CharField(max_length=255, null=True, blank=True)),
                ('meta_album', models.CharField(max_length=255, null=True, blank=True)),
                ('meta_year', models.CharField(max_length=255, null=True, blank=True)),
                ('meta_genre', models.CharField(max_length=255, null=True, blank=True)),
                ('meta_duration', models.FloatField(null=True, blank=True)),
                ('directory', models.ForeignKey(to='storage.Directory')),
            ],
        ),
    ]
