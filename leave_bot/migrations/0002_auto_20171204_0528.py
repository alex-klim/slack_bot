# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-04 05:28
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave_bot', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='token',
            field=models.CharField(max_length=200),
        ),
    ]
