# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0013_remove_bingoboard_password'),
    ]

    operations = [
        migrations.AddField(
            model_name='config',
            name='twittercard_image',
            field=models.URLField(blank=True, default='', help_text='An Image URL for a Twitter card image. (leave blank to use the default)'),
        ),
    ]
