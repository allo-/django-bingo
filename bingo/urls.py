from django.conf.urls import include, url

from . import views
from . import generic

urlpatterns = (
    url('^$', views.main, name="bingo-main"),
    url('^bingo/reclaim/$', views.reclaim_board, name="bingo-reclaim_board"),
    url('^bingo/create/$', views.create_board, name="bingo-create_board"),
    url('^bingo/vote/$', views.vote, {"ajax": False}, name="bingo-vote"),
    url('^bingo/rate/$', views.rate_game, name="bingo-rate_game"),
    url('^ajax/vote/$', views.vote, {"ajax": True}, name="bingo-vote"),
    url('^ajax/vote/(?P<board_id>[0-9]+)/$', views.vote, {"ajax": True},
        name="bingo-vote"),
    url('^bingo/(?P<board_id>[0-9]+)/$', views.bingo, name="bingo-bingo"),
    url('^wordlist/$', views.wordlist, name="bingo-wordlist"),
    url('^game/(?P<game_id>[0-9]+)/$', views.game, name="bingo-game"),
    url('^game/$', generic.GameList.as_view(), name="bingo-games_list"),
    url('^thumbnail/(?P<board_id>[0-9]+)/marked/$',
        views.thumbnail, {"marked": True}, name="bingo-thumbnail"),
    url('^thumbnail/(?P<board_id>[0-9]+)/voted/$',
        views.thumbnail, {"voted": True}, name="bingo-thumbnail"),
    url('^thumbnail/(?P<board_id>[0-9]+)/$', views.thumbnail,
        name="bingo-thumbnail"),
    url('^image/(?P<board_id>[0-9]+)/marked/$', views.image, {"marked": True},
        name="bingo-image"),
    url('^image/(?P<board_id>[0-9]+)/voted/$', views.image, {"voted": True},
        name="bingo-image"),
    url('^image/(?P<board_id>[0-9]+)/$', views.image, name="bingo-image"),
    url('^users/(?P<username>[^/]+)/$', views.profile, name="bingo-profile"),
    url('^change_theme/$', views.change_theme, name="bingo-change_theme"),
)
