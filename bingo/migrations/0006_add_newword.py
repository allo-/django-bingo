# -*- coding: utf-8 -*-


from django.db import migrations, models
import django.db.models.deletion

def split_words(apps, schema_editor):
    Word = apps.get_model("bingo", "Word")
    BingoField = apps.get_model("bingo", "BingoField")
    NewWord = apps.get_model("bingo", "NewWord")
    Site = apps.get_model("sites", "Site")
    for word in Word.objects.all():
        for site in Site.objects.all():
            fields = BingoField.objects.filter(word=word, board__game__site=site)
            if site in word.site.all():
                new_word = NewWord(word=word.word,
                    description=word.description, type=word.type, site=site)
                new_word.save()
                fields.update(new_word=new_word)
            elif fields.count() > 0:
                new_word = NewWord(word=word.word,
                    description=word.description, type=word.type, site=site,
                    enabled=False)
                new_word.save()
                fields.update(new_word=new_word)


class Migration(migrations.Migration):

    dependencies = [
        ('sites', '0002_alter_domain_unique'),
        ('bingo', '0005_changed_rating_and_vote'),
    ]

    operations = [
        migrations.CreateModel(
            name='NewWord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('word', models.CharField(max_length=255)),
                ('description', models.CharField(blank=True, max_length=255)),
                ('type', models.PositiveSmallIntegerField(choices=[(1, b'Topic'), (2, b'Middle'), (3, b'Meta')])),
                ('enabled', models.BooleanField(default=True)),
                ('site', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='sites.Site')),
            ],
            options={
                'ordering': ('word',),
            },
        ),
        migrations.AddField(
            model_name='bingofield',
            name='new_word',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='bingo.NewWord'),
        ),
        migrations.RunPython(split_words),
    ]

