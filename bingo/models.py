from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError

from colorful.fields import RGBColorField

from django.db import models


class Word(models.Model):
    """
        a word entry. Should not be deleted, but only disabled
        to preserve old BingoFields
    """
    word = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_middle = models.BooleanField(default=False)

    def __unicode__(self):
        return self.word


class Game(models.Model):
    date = models.DateTimeField(auto_now_add=True)

    def __unicode__(self):
        return _(u"Game created at {0}").format(
            self.date.strftime(u"%Y-%m-%d %H:%M"))


class BingoBoard(models.Model):
    game = models.ForeignKey("Game")
    color = RGBColorField()
    ip = models.IPAddressField(blank=True, null=True)
    user = models.ForeignKey(get_user_model(), blank=True, null=True)

    def clean(self):
        if not self.ip and not self.user:
            raise ValidationError(_(u"Game must have either an ip or an user"))

    def __unicode__(self):
        return u"BingoBoard #{0} created by {1}".format(
            self.id,
            self.user if self.user else self.ip)


def position_validator(value):
    if not (0 < value < 26):
        raise ValidationError(_(
            u"invalid position. valid values range: 1-25"))


class BingoField(models.Model):
    word = models.ForeignKey("Word")
    board = models.ForeignKey("BingoBoard")
    position = models.SmallIntegerField(validators=[position_validator])

    def is_middle(self):
        return self.position == 13

    def clean(self):
        if self.is_middle() and not self.word.is_middle:
            raise ValidationError(_(
                u"The BingoField has middle position, "
                u"but the word is no middle word"))
        elif not self.is_middle() and self.word.is_middle:
            raise ValidationError(_(
                u"The BingoField is not in the middle,"
                u"but the word is a middle word"))

    def __unicode__(self):
        return _(u"BingoField: word={0}, pos=({1},{2}){3}").format(
            self.word, self.position/5+1, self.position % 5,
            _(u" [middle]") if self.is_middle() else u"")
