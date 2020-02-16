# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0004_change_vote_field_type_to_integer'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bingoboard',
            name='rating',
            field=models.IntegerField(blank=True, choices=[(None, 'unrated'), (1, '1 stars'), (2, '2 stars'), (3, '3 stars'), (4, '4 stars'), (5, '5 stars')], default=None, null=True),
        ),
        migrations.AlterField(
            model_name='bingofield',
            name='vote',
            field=models.SmallIntegerField(default=0),
        ),
    ]
