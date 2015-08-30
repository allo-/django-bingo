# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import bingo.models
import colorful.fields
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BingoBoard',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('board_id', models.IntegerField(null=True, blank=True)),
                ('color', colorful.fields.RGBColorField(max_length=7)),
                ('ip', models.IPAddressField(null=True, blank=True)),
                ('password', models.CharField(max_length=255, null=True, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_used', models.DateTimeField(auto_now_add=True)),
                ('rating', models.IntegerField(default=None, null=True, blank=True, choices=[(None, 'nicht bewertet'), (1, '1 Sterne'), (2, '2 Sterne'), (3, '3 Sterne'), (4, '4 Sterne'), (5, '5 Sterne')])),
            ],
            options={
                'ordering': ('-board_id',),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='BingoField',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('position', models.SmallIntegerField(default=None, null=True, blank=True, validators=[bingo.models.position_validator])),
                ('vote', models.NullBooleanField(default=None)),
                ('board', models.ForeignKey(to='bingo.BingoBoard')),
            ],
            options={
                'ordering': ('board', '-position'),
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Game',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('game_id', models.IntegerField(null=True, blank=True)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('last_used', models.DateTimeField(auto_now_add=True)),
                ('site', models.ForeignKey(to='sites.Site')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Word',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('word', models.CharField(unique=True, max_length=255)),
                ('description', models.CharField(max_length=255, blank=True)),
                ('is_middle', models.BooleanField(default=False)),
                ('site', models.ManyToManyField(to='sites.Site', null=True, blank=True)),
            ],
            options={
                'ordering': ('word',),
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='game',
            unique_together=set([('game_id', 'site')]),
        ),
        migrations.AddField(
            model_name='bingofield',
            name='word',
            field=models.ForeignKey(to='bingo.Word'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bingoboard',
            name='game',
            field=models.ForeignKey(to='bingo.Game'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='bingoboard',
            name='user',
            field=models.ForeignKey(blank=True, to=settings.AUTH_USER_MODEL, null=True),
            preserve_default=True,
        ),
        migrations.AlterUniqueTogether(
            name='bingoboard',
            unique_together=set([('board_id', 'game')]),
        ),
    ]
