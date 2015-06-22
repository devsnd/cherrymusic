# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('path', models.CharField(max_length=255)),
                ('parent', models.ForeignKey(to='storage.Directory')),
            ],
        ),
        migrations.CreateModel(
            name='File',
            fields=[
                ('id', models.AutoField(primary_key=True, auto_created=True, verbose_name='ID', serialize=False)),
                ('filename', models.CharField(max_length=255)),
                ('date_updated', models.DateField(auto_now=True)),
                ('meta_track', models.IntegerField(blank=True, null=True)),
                ('meta_track_total', models.IntegerField(blank=True, null=True)),
                ('meta_title', models.CharField(max_length=255, blank=True, null=True)),
                ('meta_artist', models.CharField(max_length=255, blank=True, null=True)),
                ('meta_album', models.CharField(max_length=255, blank=True, null=True)),
                ('meta_year', models.IntegerField(blank=True, null=True)),
                ('meta_genre', models.CharField(max_length=255, blank=True, null=True)),
                ('meta_duration', models.FloatField(blank=True, null=True)),
                ('directory', models.ForeignKey(to='storage.Directory')),
            ],
        ),
    ]
