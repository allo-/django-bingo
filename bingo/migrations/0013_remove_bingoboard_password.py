# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0012_config_bingo_description'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='bingoboard',
            name='password',
        ),
    ]
