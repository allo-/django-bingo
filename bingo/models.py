from django.contrib.auth import get_user_model
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.sites.models import Site

from colorful.fields import RGBColorField

from random import randint
from datetime import datetime
import pytz

TIMEZONE = getattr(settings, "TIMEZONE", "UTC")

# Color ranges
COLOR_FROM = getattr(settings, "COLOR_FROM", 80)
COLOR_TO = getattr(settings, "COLOR_TO", 160)

# Expire game after hard-timeout seconds, or
# soft-timeout seconds inactivity, whatever comes first.
GAME_SOFT_TIMEOUT = getattr(settings, "GAME_SOFT_TIMEOUT", 60)
GAME_HARD_TIMEOUT = getattr(settings, "GAME_HARD_TIMEOUT", 120)

# Time range, in which a game can be started. None = no limit
# or a ((Hour, Minute), (Hour, Minute)) tuple defining the range.
GAME_START_TIMES = getattr(settings, "GAME_START_TIMES", None)

BINGO_DATETIME_FORMAT = getattr(
    settings, "BINGO_DATETIME_FORMAT", "%Y-%m-%d %H:%M")

# if a user did not vote/refresh his board for this time,
# he is counted as inactive
USER_ACTIVE_TIMEOUT = getattr(settings, "USER_ACTIVE_TIMEOUT", 5)


def is_starttime():
    if GAME_START_TIMES is None:
        return True
    else:
        now = timezone.localtime(timezone.now()).replace(
            tzinfo=pytz.timezone(TIMEZONE))
        start, end = GAME_START_TIMES

        start_time = datetime(
            now.year, now.month, now.day,
            start[0], start[1], tzinfo=pytz.timezone(TIMEZONE))
        end_time = datetime(
            now.year, now.month, now.day,
            end[0], end[1], tzinfo=pytz.timezone(TIMEZONE))

        # game ends in the future
        if end_time > now:
            # game starts today before the end
            if start_time < end_time:
                pass
            # game started yesterday
            else:
                start_time = start_time - timezone.timedelta(1)
        # game ends tomorrow or has already ended.
        else:
            # start started today, and has already ended
            if end_time > start_time:
                pass
            # game will end tomorrow
            else:
                end_time = end_time + timezone.timedelta(1)

        return start_time <= now and now <= end_time


class Word(models.Model):
    """
        a word entry. Should not be deleted, but only disabled
        to preserve old BingoFields
    """
    word = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    is_middle = models.BooleanField(default=False)
    site = models.ManyToManyField(Site)

    def __unicode__(self):
        return u"Word: " + self.word


class TimeRangeError(Exception):
    pass


def get_game(site, create=False):
    """
        get the current game. creates a new one, if the old one is expired.
        @param create: create a game, if there is no active game
    """

    game = None
    games = Game.objects.filter(site=site).order_by("-created")

    # no game, yet, or game expired
    if (games.count() == 0 or games[0].is_expired()):
        if create:
            if is_starttime():
                game = Game(site=site)
                game.save()
            else:
                raise TimeRangeError(
                    _(u"game start outside of the valid timerange"))
    else:
        game = games[0]

    return game


class Game(models.Model):
    game_id = models.IntegerField(blank=True, null=True)
    site = models.ForeignKey(Site)
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ("game_id", "site")

    def __unicode__(self):
        return _(u"Game created at {0} (site {1})").format(
            timezone.localtime(self.created).strftime(u"%Y-%m-%d %H:%M"),
            self.site)

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

    def num_users(self):
        return self.bingoboard_set.count()

    def num_active_users(self):
        return self.bingoboard_set.exclude(
            last_used__lte=timezone.now()
            - timezone.timedelta(0, 60 * USER_ACTIVE_TIMEOUT)
        ).count()

    def save(self):
        if self.pk is None:
            games = Game.objects.filter(site=self.site)
            current_id = games.aggregate(
                max_id=models.Max('game_id'))['max_id']
            if current_id is None:
                self.game_id = 1
            else:
                self.game_id = current_id + 1
        return super(Game, self).save()


def _get_random_words(site):
    all_words = Word.objects.filter(site=site, is_active=True).order_by("?")
    middle_words = all_words.filter(site=site, is_middle=True).order_by("?")
    words = all_words.filter(is_middle=False)
    if middle_words.count() == 0:
        raise ValidationError(_(u"No middle words in database"))
    middle = middle_words[0]
    if words.count() < 24:
        raise ValidationError(_(u"Not enough (non-middle) words in database"))
    return list(words), middle


class BingoBoard(models.Model):
    board_id = models.IntegerField(blank=True, null=True)
    game = models.ForeignKey("Game")
    color = RGBColorField()
    ip = models.IPAddressField(blank=True, null=True)
    user = models.ForeignKey(get_user_model(), blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now=True)

    def save(self):
        if self.ip is None and self.user is None:
            raise ValidationError(
                _(u"BingoBoard must have either an ip or an user"))

        if self.pk is None:
            # unique_together for optional fields
            game_boards = BingoBoard.objects.filter(game=self.game)
            if not self.user is None:
                if game_boards.filter(user=self.user).count() > 0:
                    raise ValidationError(
                        _(u"game and user must be unique_together"))
            if not self.ip is None:
                if game_boards.filter(ip=self.ip).count() > 0:
                    raise ValidationError(
                        _(u"game and ip must be unique_together"))

            # get the board_id
            bingo_boards = BingoBoard.objects.filter(
                game__site=self.game.site)
            current_id = bingo_boards.aggregate(
                max_id=models.Max('board_id'))['max_id']
            if current_id is None:
                self.board_id = 1
            else:
                self.board_id = current_id + 1

            # generate a color
            self.color = "#%x%x%x" % (
                randint(COLOR_FROM, COLOR_TO),
                randint(COLOR_FROM, COLOR_TO),
                randint(COLOR_FROM, COLOR_TO))
            # first create the fields, so the board will
            # not be saved, when field creation fails
            fields = self.create_bingofields()
            # create the board
            super(BingoBoard, self).save()
            # now that the board has a pk, save the fields
            for field in fields:
                field.board = self
                field.save()
        else:
            super(BingoBoard, self).save()

    def create_bingofields(self):
        count = 0
        words, middle = _get_random_words(site=self.game.site)
        fields = []
        for i in xrange(25):
            # 13th field = middle
            if i == 12:
                fields.append(BingoField(word=middle, position=i+1))
            else:
                fields.append(BingoField(word=words[count], position=i+1))
                count += 1
        # create fields without position for every
        # active word, which is not on the board, too.
        for word in words[25:]:
            fields.append(BingoField(word=word, position=None))

        return fields

    def get_board_fields(self):
        return self.bingofield_set.exclude(position=None).order_by("position")

    def get_all_word_fields(self):
        return self.bingofield_set.filter(word__is_middle=False)

    def get_created(self):
        """
            get created field with BINGO_DATETIME_FORMAT formatting
        """
        return timezone.localtime(self.created).strftime(BINGO_DATETIME_FORMAT)

    def get_last_used(self):
        """
            get last_used field with BINGO_DATETIME_FORMAT formatting
        """
        return self.last_used.strftime(BINGO_DATETIME_FORMAT)

    def __unicode__(self):
        return _(u"BingoBoard #{0} created by {1} (site {2})").format(
            self.board_id,
            self.user if self.user else self.ip,
            self.game.site)


def position_validator(value):
    if not value is None and not (0 < value < 26):
        raise ValidationError(_(
            _(u"invalid position. valid values range: 1-25 or None")))


class BingoField(models.Model):
    word = models.ForeignKey("Word")
    board = models.ForeignKey("BingoBoard")
    position = models.SmallIntegerField(
        validators=[position_validator],
        blank=True, null=True, default=None)
    vote = models.NullBooleanField(default=None)

    class Meta:
        ordering = ("board", "-position")

    def is_middle(self):
        return self.position == 13

    def num_votes(self):
        fields = BingoField.objects.filter(
            board__game=self.board.game, word=self.word)
        positive = fields.filter(vote=True).count()
        negative = fields.filter(vote=False).count()
        return max(0, positive - negative)

    def clean(self):
        if self.is_middle() and not self.word.is_middle:
            raise ValidationError(_(
                u"The BingoField has middle position, "
                u"but the word is no middle word"))
        elif not self.is_middle() and self.word.is_middle:
            raise ValidationError(_(
                u"The BingoField is not in the middle, "
                u"but the word is a middle word"))

    def __unicode__(self):
        if self.position is not None:
            return _(u"BingoField: word={0}, pos=({1},{2}){3})").format(
                self.word, self.position/5+1, self.position % 5,
                _(u" [middle]") if self.is_middle() else u"")
        else:
            return _(u"BingoField: word={0}, (not on the board)").format(
                self.word)
