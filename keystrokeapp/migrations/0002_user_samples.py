# -*- coding: utf-8 -*-
# Generated by Django 1.11 on 2017-04-14 16:58
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('keystrokeapp', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='samples',
            field=models.IntegerField(default=2),
            preserve_default=False,
        ),
    ]
