from django.views.generic import ListView
from django.contrib.sites.models import Site
from django.contrib.sites.shortcuts import get_current_site

from .models import Game


class GameList(ListView):
    paginate_by = 25
    def get_queryset(self):
        return Game.objects.filter(
            site=get_current_site(self.request)).exclude(
            bingoboard=None).order_by("-created")
