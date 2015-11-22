# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def forwards(apps, schema_editor):
    Word = apps.get_model("bingo", "Word")
    for word in Word.objects.all():
        if word.is_middle:
            word.type = 2
        else:
            word.type = 1
        word.save()

def backwards(apps, schema_editor):
    Word = apps.get_model("bingo", "Word")
    for word in Word.objects.all():
        if word.type == 2:
            word.is_middle = True
        else:
            word.is_middle = False
        word.save()

class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0002_auto_django_1_8_compatiblity'),
    ]

    operations = [
        migrations.AddField(
            model_name='word',
            name='type',
            field=models.PositiveSmallIntegerField(default=1, choices=[(1, b'Topic'), (2, b'Middle'), (3, b'Meta')]),
            preserve_default=False,
        ),
        migrations.RunPython(
            forwards,
            backwards
        ),
        migrations.RemoveField(
            model_name='word',
            name='is_middle',
        ),
    ]
