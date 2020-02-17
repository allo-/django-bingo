# -*- coding: utf-8 -*-


from django.db import migrations, models


def forwards(apps, schema_editor):
    BingoField = apps.get_model("bingo", "BingoField")
    BingoField.objects.filter(vote=None).update(vote_new=0)
    BingoField.objects.filter(vote=True).update(vote_new=1)
    BingoField.objects.filter(vote=False).update(vote_new=-1)


class Migration(migrations.Migration):

    dependencies = [
        ('bingo', '0003_word_types'),
    ]

    operations = [
        migrations.AddField(
            model_name='bingofield',
            name='vote_new',
            field=models.SmallIntegerField(default=0),
            preserve_default=False,
        ),
        migrations.RunPython(
            forwards
        ),
        migrations.RemoveField(
            model_name='bingofield',
            name='vote',
        ),
        migrations.RenameField(
            model_name='bingofield',
            old_name='vote_new',
            new_name='vote',
        ),
    ]
