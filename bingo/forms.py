from django import forms
from django.utils.translation import pgettext, ugettext as _
from django.conf import settings
from django.contrib.auth.hashers import get_hasher

from models import BingoBoard, is_starttime
from times import is_starttime


SALT = getattr(settings, "SALT", "hackme")
GAME_START_TIMES = getattr(settings, "GAME_START_TIMES", None)

GAME_START_DISABLED = getattr(
    settings, "GAME_START_DISABLED", False)
GAME_DESCRIPTION_DISABLED = getattr(
    settings, "GAME_DESCRIPTION_DISABLED", False)


class CreateForm(forms.Form):
    password = forms.CharField(label=_(u"Password (optional)"),
                               widget=forms.PasswordInput(),
                               required=False)

    def __init__(self, *args, **kwargs):
        game = kwargs.get('game')
        # forms.Form throws an error on additional kwargs
        if 'game' in kwargs:
            del kwargs['game']
        super(CreateForm, self).__init__(*args, **kwargs)

        # add a game description field to the create form,
        # when there is no active game.
        if not GAME_DESCRIPTION_DISABLED and game is None:
            self.fields['description'] = forms.CharField(
                label=_(u'Game Description (optional)'),
                required=False)

    def clean_password(self):
        if self.cleaned_data['password']:
            hasher = get_hasher(algorithm='sha1')
            hashed_password = hasher.encode(
                self.cleaned_data['password'], SALT)
            return hashed_password
        else:
            return None

    def clean(self):
        if GAME_START_DISABLED:
            raise forms.ValidationError(
                _(u"Starting new games is disabled."))

        if not is_starttime():
            start, end = GAME_START_TIMES
            start_time_str = "{0}:{1}".format(
                str(start[0]).zfill(2),
                str(start[1]).zfill(2))
            end_time_str = "{0}:{1}".format(
                str(end[0]).zfill(2),
                str(end[1]).zfill(2))

            raise forms.ValidationError(
                _(u"Games can only be started between {0} and {1}.").format(
                    start_time_str, end_time_str))

        return super(CreateForm, self).clean()


class ReclaimForm(forms.Form):
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
                                                 password=hashed_password)
        if bingo_boards.count() > 0:
            # if two users have the same password,
            # just return the first board.
            self.cleaned_data['bingo_board'] = bingo_boards[0]
        else:
            raise forms.ValidationError(
                _(u"No active board with this password."
                    " Try again, or create a new one."))
        return hashed_password


class ChangeThemeForm(forms.Form):
    theme = forms.CharField(required=False)


class RateGameForm(forms.Form):
    rating = forms.ChoiceField(
        choices=zip(["None"] + range(1, 6), [_("n/a")] + range(1, 6)))
