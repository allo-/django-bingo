from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.db import models

from colorful.fields import RGBColorField

from random import randint

COLOR_FROM = getattr(settings, "COLOR_FROM", 80)
COLOR_TO = getattr(settings, "COLOR_TO", 160)
GAME_SOFT_TIMEOUT = getattr(settings, "GAME_SOFT_TIMEOUT", 120)
GAME_HARD_TIMEOUT = getattr(settings, "GAME_HARD_TIMEOUT", 300)


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
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    def __unicode__(self):
        return _(u"Game created at {0}").format(
            self.created.strftime(u"%Y-%m-%d %H:%M"))

    def is_expired(self):
        # game expired, because no one used it
        if (timezone.now() - self.last_used).seconds \
                > (GAME_SOFT_TIMEOUT * 60):
            return True
        # game expired, because its too old, even when someone is using it
        elif (timezone.now() - self.created).seconds \
                > (GAME_HARD_TIMEOUT * 60):
            return True
        else:
            return False


def get_random_words():
    words = Word.objects.order_by("?")
    middle_words = words.filter(is_active=True, is_middle=True).order_by("?")
    if middle_words.count() == 0:
        raise ValidationError(_(u"No middle words in database"))
    middle = middle_words[0]
    words = words.filter(is_active=True, is_middle=False)[:24]
    if words.count() < 24:
        raise ValidationError(_(u"Not enough words in database"))
    return list(words), middle


class BingoBoard(models.Model):
    game = models.ForeignKey("Game")
    color = RGBColorField()
    ip = models.IPAddressField(blank=True, null=True)
    user = models.ForeignKey(get_user_model(), blank=True, null=True)
    password = models.CharField(max_length=255)

    def clean(self):
        if self.ip is None and self.user is None:
            raise ValidationError(
                _(u"BingoBoard must have either an ip or an user"))

    def save(self):
        if self.ip is None and self.user is None:
            raise ValidationError(
                _(u"BingoBoard must have either an ip or an user"))

        if self.pk is None:
            if not self.user is None:
                if BingoBoard.objects.filter(game=self.game,
                                             user=self.user).count() > 0:
                    raise ValidationError(
                        _(u"game and user must be unique_together"))
            if not self.ip is None:
                if BingoBoard.objects.filter(game=self.game,
                                             ip=self.ip).count() > 0:
                    raise ValidationError(
                        _(u"game and ip must be unique_together"))

            self.color = "#%x%x%x" % (
                randint(COLOR_FROM, COLOR_TO),
                randint(COLOR_FROM, COLOR_TO),
                randint(COLOR_FROM, COLOR_TO))
            super(BingoBoard, self).save()
            self.create_bingofields()
        else:
            super(BingoBoard, self).save()

    def create_bingofields(self):
        count = 0
        words, middle = get_random_words()
        for i in xrange(25):
            if i == 12:
                BingoField(word=middle, board=self, position=i+1).save()
            else:
                BingoField(word=words[count], board=self, position=i+1).save()
                count += 1

    def __unicode__(self):
        return _(u"BingoBoard #{0} created by {1}").format(
            self.id,
            self.user if self.user else self.ip)


def position_validator(value):
    if not (0 < value < 26):
        raise ValidationError(_(
            _(u"invalid position. valid values range: 1-25")))


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
