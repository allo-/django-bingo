from django import forms
from django.utils.translation import pgettext, ugettext as _
from django.conf import settings
from django.contrib.auth.hashers import get_hasher

from .models import BingoBoard
from . import times
from .times import is_starttime
from . import config


class CreateForm(forms.Form):

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


class ChangeThemeForm(forms.Form):
    theme = forms.CharField(required=False)


class RateGameForm(forms.Form):
    rating = forms.ChoiceField(
        choices=list(zip(["None"] + list(range(1, 6)), [_("n/a")] + list(range(1, 6)))))
