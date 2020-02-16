# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0007_remove_word'),
    ]

    operations = [
        migrations.RenameModel(
            old_name='NewWord',
            new_name='Word',
        ),
        migrations.RenameField(
            model_name='bingofield',
            old_name='new_word',
            new_name='word',
        ),
    ]
