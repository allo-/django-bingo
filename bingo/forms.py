from django import forms
from django.utils.translation import pgettext, ugettext as _
from django.conf import settings
from django.contrib.auth.hashers import get_hasher

from .models import BingoBoard
from . import times
from .times import is_starttime
from . import config


SALT = getattr(settings, "SALT", "hackme")


class CreateForm(forms.Form):
    password = forms.CharField(label=_("Password (optional)"),
                               widget=forms.PasswordInput(),
                               required=False)

    def __init__(self, site, *args, **kwargs):
        game = kwargs.get('game')
        # forms.Form throws an error on additional kwargs
        if 'game' in kwargs:
            del kwargs['game']
        super(CreateForm, self).__init__(*args, **kwargs)

        # add a game description field to the create form,
        # when there is no active game.
        if config.get("description_enabled", site=site) and game is None:
            self.fields['description'] = forms.CharField(
                label=_('Game Description (optional)'),
                required=False)
        self.site = site

    def clean_password(self):
        if self.cleaned_data['password']:
            hasher = get_hasher(algorithm='sha1')
            hashed_password = hasher.encode(
                self.cleaned_data['password'], SALT)
            return hashed_password
        else:
            return None

    def clean(self):
        if not config.get("start_enabled", site=self.site):
            raise forms.ValidationError(
                _("Starting new games is disabled."))

        _now = times.now()
        game_week_days = {
            0: config.get("week_days_monday", site=self.site),
            1: config.get("week_days_tuesday", site=self.site),
            2: config.get("week_days_wednesday", site=self.site),
            3: config.get("week_days_thursday", site=self.site),
            4: config.get("week_days_friday", site=self.site),
            5: config.get("week_days_saturday", site=self.site),
            6: config.get("week_days_sunday", site=self.site)
        }
        if not game_week_days[_now.weekday()]:
            raise forms.ValidationError(_("Games cannot be started at this day of week."))
        if not is_starttime(self.site):
            start_time_begin = config.get("start_time_begin", site=self.site)
            start_time_end = config.get("start_time_end", site=self.site)
            start_time_str = "{0}:{1}".format(
                str(start_time_begin.hour).zfill(2),
                str(start_time_begin.minute).zfill(2))
            end_time_str = "{0}:{1}".format(
                str(start_time_end.hour).zfill(2),
                str(start_time_end.minute).zfill(2))

            raise forms.ValidationError(
                _("Games can only be started between {0} and {1}.").format(
                    start_time_str, end_time_str))

        return super(CreateForm, self).clean()


class ReclaimForm(forms.Form):
    """
        Reclaim a board for the current game using the password.
        Works only for anonymous users.
    """
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, data=None, game=None, *args, **kwargs):
        self.game = game
        super(ReclaimForm, self).__init__(data=data, *args, **kwargs)

    def clean_password(self):
        hasher = get_hasher(algorithm='sha1')
        hashed_password = hasher.encode(self.cleaned_data['password'],
                                        SALT)
        if not self.game or self.game.is_expired():
            raise forms.ValidationError(
                _("The game is expired, please create a new board."))
        bingo_boards = BingoBoard.objects.filter(game=self.game,
                                                 password=hashed_password,
                                                 user=None)
        if bingo_boards.count() > 0:
            # if two users have the same password,
            # just return the first board.
            self.cleaned_data['bingo_board'] = bingo_boards[0]
        else:
            raise forms.ValidationError(
                _("No active board with this password."
                    " Try again, or create a new one."))
        return hashed_password


class ClaimForm(forms.Form):
    """
        Reclaim all old boards with the given password and assign them to
        a the user
    """
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, data=None, user=None, *args, **kwargs):
        self.user = user
        super(ClaimForm, self).__init__(data=data, *args, **kwargs)

    def clean_password(self):
        hasher = get_hasher(algorithm='sha1')
        hashed_password = hasher.encode(self.cleaned_data['password'],
                                        SALT)

        bingo_boards = BingoBoard.objects.filter(
            password=hashed_password).select_related()

        # check, that no User gets two BingoBoards from the same Game,
        # just because another User used the same password.
        # Games, which contain two BingoBoards with the given password
        # are filtered, so these BingoBoards cannot be claimed by anyone.
        game_ids = set()
        duplicate_game_ids = set()
        for board in bingo_boards:
            if board.game.id in game_ids:
                duplicate_game_ids.add(board.game.id)
            else:
                game_ids.add(board.game.id)

        # filter for user=None to prevent stealing already claimed boards
        bingo_boards.exclude(
            game__id__in=duplicate_game_ids).filter(
            user=None).update(user=self.user)

        return hashed_password


class ChangeThemeForm(forms.Form):
    theme = forms.CharField(required=False)


class RateGameForm(forms.Form):
    rating = forms.ChoiceField(
        choices=list(zip(["None"] + list(range(1, 6)), [_("n/a")] + list(range(1, 6)))))
