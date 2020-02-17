# -*- coding: utf-8 -*-


from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='bingoboard',
            name='ip',
            field=models.GenericIPAddressField(null=True, blank=True),
        ),
        migrations.AlterField(
            model_name='word',
            name='site',
            field=models.ManyToManyField(to='sites.Site', blank=True),
        ),
    ]
