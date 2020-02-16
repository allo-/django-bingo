# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0006_add_newword'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='word',
            name='site',
        ),
        migrations.RemoveField(
            model_name='bingofield',
            name='word',
        ),
        migrations.DeleteModel(
            name='Word',
        ),
    ]
