# -*- coding: utf-8 -*-
# Generated by Django 1.11.7 on 2017-12-03 22:07
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('leave_bot', '0002_auto_20171203_2157'),
    ]

    operations = [
        migrations.AlterField(
            model_name='token',
            name='token',
            field=models.CharField(max_length=150),
        ),
    ]