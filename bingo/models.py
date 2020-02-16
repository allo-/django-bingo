from django.contrib.auth.models import User
from django.utils.translation import ugettext as _
from django.core.exceptions import ValidationError
from django.conf import settings
from django.utils import timezone
from django.db import models, transaction
from django.db.models import Count, Sum
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.urlresolvers import reverse

from colorful.fields import RGBColorField

from random import randint

from times import is_starttime, is_after_endtime, get_endtime


# Color ranges
COLOR_FROM = getattr(settings, "COLOR_FROM", 80)
COLOR_TO = getattr(settings, "COLOR_TO", 160)

# Expire game after hard-timeout seconds, or
# soft-timeout seconds inactivity, whatever comes first.
GAME_SOFT_TIMEOUT = getattr(settings, "GAME_SOFT_TIMEOUT", 60)
GAME_HARD_TIMEOUT = getattr(settings, "GAME_HARD_TIMEOUT", 120)

BINGO_IMAGE_DATETIME_FORMAT = getattr(
    settings, "BINGO_IMAGE_DATETIME_FORMAT", "%Y-%m-%d %H:%M")

# if a user did not vote/refresh his board for this time,
# he is counted as inactive
USER_ACTIVE_TIMEOUT = getattr(settings, "USER_ACTIVE_TIMEOUT", 5)

THUMBNAILS_ENABLED = getattr(settings, "THUMBNAILS_ENABLED", True)

WORD_TYPE_TOPIC = 1
WORD_TYPE_MIDDLE = 2
WORD_TYPE_META = 3
WORD_TYPES = (
    (WORD_TYPE_TOPIC, 'Topic'),
    (WORD_TYPE_MIDDLE, 'Middle'),
    (WORD_TYPE_META, 'Meta'),
)


class Word(models.Model):
    """
        a word entry. Should not be deleted, but only disabled
        to preserve old BingoFields
    """
    word = models.CharField(max_length=255)
    description = models.CharField(max_length=255, blank=True)
    type = models.PositiveSmallIntegerField(choices=WORD_TYPES)
    site = models.ForeignKey(Site, blank=True, null=True)
    enabled = models.BooleanField(default=True)

    class Meta:
        ordering = ("word",)
        #unique_together = ("word", "site")

    def __unicode__(self):
        return u"Word: " + self.word


class TimeRangeError(Exception):
    pass


def get_game(site, description="", create=False):
    """
        get the current game, if its still active, else
        creates a new game, if the current time is inside the
        GAME_START_TIMES interval and create=True
        @param create: create a game, if there is no active game
        @returns: None if there is no active Game, and none shoul be
        created or the (new) active Game.
    """

    game = None
    games = Game.objects.filter(site=site).order_by("-created")
    try:
        game = games[0]
    except IndexError:
        game = None

    # no game, yet, or game expired
    if game is None or game.is_expired() or is_after_endtime():
        if create:
            if is_starttime():
                game = Game(site=site, description=description)
                game.save()
            else:
                raise TimeRangeError(
                    _(u"game start outside of the valid timerange"))
        else:
            game = None

    # game exists and its not after the GAME_END_TIME
    elif not is_after_endtime():
        game = games[0]

    return game


class Game(models.Model):
    game_id = models.IntegerField(blank=True, null=True)
    description = models.CharField(max_length=255, blank=True)
    site = models.ForeignKey(Site)
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("game_id", "site")

    def get_absolute_url(self):
        return reverse('bingo.views.game', kwargs={"game_id": self.game_id})

    def __unicode__(self):
        return _(u"Game #{0} created at {1} (site {2})").format(
            self.game_id,
            timezone.localtime(self.created).strftime(u"%Y-%m-%d %H:%M"),
            self.site)

    def hard_expiry(self):
        if GAME_HARD_TIMEOUT is not None:
            return self.created + timezone.timedelta(0, GAME_HARD_TIMEOUT * 60)

    def soft_expiry(self):
        if GAME_SOFT_TIMEOUT is not None:
            return self.last_used + timezone.timedelta(
                0, GAME_SOFT_TIMEOUT * 60)

    def end_time(self):
        hard_expiry = self.hard_expiry()
        end_time = get_endtime()
        if hard_expiry is not None and end_time is not None:
            return min(end_time, hard_expiry)
        elif hard_expiry is None:
            # may be None
            return end_time
        else:
            # may be None
            return hard_expiry

    def is_expired(self):
        # game expired, because no one used it
        now = timezone.now()
        diff_last_used = now - self.last_used
        diff_created = now - self.created

        seconds_since_last_used = \
            diff_last_used.days * 24 * 60 * 60 + diff_last_used.seconds
        seconds_since_created = \
            diff_created.days * 24 * 60 * 60 + diff_created.seconds

        # game expired, because nobody used it
        if GAME_SOFT_TIMEOUT and seconds_since_last_used \
                > (GAME_SOFT_TIMEOUT * 60):
            return True

        # game expired, because its too old, even when someone is using it
        elif GAME_HARD_TIMEOUT and seconds_since_created \
                > (GAME_HARD_TIMEOUT * 60):
            return True
        else:
            return False

    def num_users(self):
        return self.bingoboard_set.count()

    def num_active_users(self):
        if USER_ACTIVE_TIMEOUT:
            return self.bingoboard_set.exclude(
                last_used__lte=timezone.now()
                - timezone.timedelta(0, 60 * USER_ACTIVE_TIMEOUT)
            ).count()
        else:
            return self.num_users()

    def words_with_votes(self, only_topics=True):
        """
            returns a list with words ordered by the number of votes
            annotated with the number of votes in the "votes" property.
        """
        result = Word.objects.filter(
            bingofield__board__game__id=self.id).exclude(
            type=WORD_TYPE_MIDDLE)

        if only_topics:
            result = result.exclude(bingofield__word__type=WORD_TYPE_META)

        result = result.annotate(
            votes=Sum("bingofield__vote")).order_by("-votes").values()

        for item in result:
            item['votes'] = max(0, item['votes'])
            if result[0]['votes'] != 0:
                item['percent'] = float(item['votes']) / result[0]['votes'] * 100
            else:
                item['percent'] = 0
        return result

    def all_words_with_votes(self):
        return self.words_with_votes(only_topics=False)

    def rating(self):
        return self.bingoboard_set.exclude(rating=None).aggregate(
            rating=models.Avg('rating'))['rating'] or 0

    def num_ratings(self):
        return self.bingoboard_set.exclude(rating=None).aggregate(
            num=models.Count('rating'))['num']

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
    all_words = Word.objects.filter(site=site, enabled=True).order_by("?")
    middle_words = all_words.filter(site=site, type=WORD_TYPE_MIDDLE).order_by("?")
    words = all_words.exclude(type=WORD_TYPE_MIDDLE)
    if middle_words.count() == 0:
        raise ValidationError(_(u"No middle words in database"))
    middle = middle_words[0]
    if words.count() < 24:
        raise ValidationError(_(u"Not enough (non-middle) words in database"))
    return list(words), middle


RATINGS = (
    (None, _("unrated")),
    (1, _("{0} stars").format(1)),
    (2, _("{0} stars").format(2)),
    (3, _("{0} stars").format(3)),
    (4, _("{0} stars").format(4)),
    (5, _("{0} stars").format(5))
)


class BingoBoard(models.Model):
    board_id = models.IntegerField(blank=True, null=True)
    game = models.ForeignKey("Game")
    color = RGBColorField()
    ip = models.GenericIPAddressField(blank=True, null=True)
    user = models.ForeignKey(User, blank=True, null=True)
    password = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(auto_now_add=True)
    rating = models.IntegerField(choices=RATINGS, null=True, blank=True,
        default=None)

    class Meta:
        ordering = ("-board_id",)
        # board_id, game__site is not possible
        unique_together = ("board_id", "game")

    def get_absolute_url(self):
        return reverse('bingo.views.bingo', kwargs={"board_id": self.board_id})

    def clean(self):
        try:
            board = BingoBoard.objects.get(
                board_id=self.board_id, game__site=self.game.site)
            # if its not an edit of the same BingoBoard
            if board.pk != self.pk:
                raise ValidationError(
                    _(u"BingoBoard ID not unique for site {0}").format(
                        self.game.site))
        except BingoBoard.DoesNotExist:
            return  # everything okay

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
            # ip only needs to be unique for anonymous users
            # to check if the ip is relevant:
            # - check the current board does not have an user
            # - filter for existing boards from this ip only with user=None
            if not self.ip is None and not self.user:
                if game_boards.filter(ip=self.ip, user=None).count() > 0:
                    raise ValidationError(
                        _(u"game and ip must be unique_together"))

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

            # then create a board_id as atomic as possible for two fields,
            # which need to be unique together
            bingo_boards = BingoBoard.objects.filter(
                game__site=self.game.site)
            current_id = bingo_boards.aggregate(
                max_id=models.Max('board_id'))['max_id']
            new_id = current_id + 1 if current_id else 1
            BingoBoard.objects.filter(id=self.id).update(
                board_id=new_id)

            # set the id for the current instance
            self.board_id = new_id

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
        # the index is 24, because there are only 24
        # non-middle words on the field
        assert count == 24
        for word in words[24:]:
            fields.append(BingoField(word=word, position=None))

        return fields

    def get_board_fields(self):
        return self.bingofield_set.exclude(position=None).order_by("position")

    def get_all_word_fields(self):
        return self.bingofield_set.exclude(word__type=WORD_TYPE_MIDDLE)

    def get_middle_field(self):
        return self.bingofield_set.filter(word__type=WORD_TYPE_MIDDLE)[0]

    def get_created(self):
        """
            get created field with BINGO_IMAGE_DATETIME_FORMAT formatting
        """
        return timezone.localtime(self.created).strftime(
            BINGO_IMAGE_DATETIME_FORMAT)

    def get_last_used(self):
        """
            get last_used field with BINGO_IMAGE_DATETIME_FORMAT formatting
        """
        return timezone.localtime(self.last_used).strftime(
            BINGO_IMAGE_DATETIME_FORMAT)

    def thumbnails_enabled(self):
        return THUMBNAILS_ENABLED

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
    word = models.ForeignKey("Word", blank=True, null=True)
    board = models.ForeignKey("BingoBoard")
    position = models.SmallIntegerField(
        validators=[position_validator],
        blank=True, null=True, default=None)
    vote = models.SmallIntegerField(default=0)

    class Meta:
        ordering = ("board", "-position")

    def is_middle(self):
        return self.position == 13

    def num_votes(self):
        if self.word.type == WORD_TYPE_MIDDLE:
            return 0
        vote_counts_cachename = 'vote_counts_game={0:d}'.format(
            self.board.game.id)
        vote_counts = cache.get(vote_counts_cachename, None)
        if not vote_counts or not self.word.id in vote_counts:
            votes = Word.objects.exclude(type=WORD_TYPE_MIDDLE).filter(
                bingofield__board__game=self.board.game).annotate(
                votes=Sum('bingofield__vote')).values("id", "votes")

            vote_counts = {}
            for vote in votes:
                vote_counts[vote['id']] = vote['votes']
            cache.set(vote_counts_cachename, vote_counts)
        return max(0, vote_counts.get(self.word.id, 0))

    def clean(self):
        if self.is_middle() and self.word.type != WORD_TYPE_MIDDLE:
            raise ValidationError(_(
                u"The BingoField has middle position, "
                u"but the word is no middle word"))
        elif not self.is_middle() and self.word.type == WORD_TYPE_MIDDLE:
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
