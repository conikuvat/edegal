# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2018-09-17 06:51
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('edegal', '0007_remove_mediaspec_is_default_thumbnail'),
    ]

    operations = [
        migrations.AddField(
            model_name='mediaspec',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]