# -*- coding: utf-8 -*-
# Generated by Django 1.9.6 on 2016-11-04 15:29
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('newsroom', '0030_author_password_reset'),
    ]

    operations = [
        migrations.RenameField(
            model_name='author',
            old_name='password_reset',
            new_name='password_changed',
        ),
    ]
