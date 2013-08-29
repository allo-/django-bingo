from django.views.generic import ListView
from django.contrib.sites.models import Site

from models import Game


class GameList(ListView):
    queryset = Game.objects.filter(
        site=Site.objects.get_current()).exclude(
        bingoboard=None).order_by("-created")
    paginate_by = 25
