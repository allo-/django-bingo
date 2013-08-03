from django import forms
from django.utils.translation import ugettext as _

from models import BingoBoard


class CreateForm(forms.Form):
    password = forms.CharField(label=_(u"Password (optional)"),
                               widget=forms.PasswordInput(),
                               required=False)


class ReclaimForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, data=None, game=None):
        self.game = game
        super(ReclaimForm, self).__init__(data)

    def clean_password(self):
        password = self.cleaned_data['password']
        if not self.game or self.game.is_expired():
            raise forms.ValidationError(
                _("The game is expired, please create a new field"))
        bingo_boards = BingoBoard.objects.filter(game=self.game,
                                                 password=password)
        if bingo_boards.count() > 0:
            # if two users have the same password,
            # just return the first board.
            self.cleaned_data['bingo_board'] = bingo_boards[0]
        else:
            raise forms.ValidationError(
                _(u"No active board with this password."
                    " Try again, or create a new one."))
