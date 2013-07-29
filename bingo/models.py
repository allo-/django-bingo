from django.db import models


class Word(models.Model):
    word = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.word
