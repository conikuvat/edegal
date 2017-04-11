# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-11 05:54
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('edegal', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='album',
            name='cover_picture',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='+', to='edegal.Picture'),
        ),
    ]