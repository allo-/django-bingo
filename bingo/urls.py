from django.conf.urls import patterns, include, url

import views
import generic

urlpatterns = patterns(
    '',
    url('^$', views.main),
    url('^bingo/reclaim/$', views.reclaim_board),
    url('^bingo/create/$', views.create_board),
    url('^bingo/vote/$', views.vote, {"ajax": False}),
    url('^bingo/rate/$', views.rate_game),
    url('^ajax/vote/$', views.vote, {"ajax": True}),
    url('^ajax/vote/(?P<board_id>[0-9]+)/$', views.vote, {"ajax": True}),
    url('^bingo/(?P<board_id>[0-9]+)/$', views.bingo),
    url('^game/(?P<game_id>[0-9]+)/$', views.game),
    url('^game/$', generic.GameList.as_view(), name="games_list"),
    url('^thumbnail/(?P<board_id>[0-9]+)/marked/$',
        views.thumbnail, {"marked": True}),
    url('^thumbnail/(?P<board_id>[0-9]+)/voted/$',
        views.thumbnail, {"voted": True}),
    url('^thumbnail/(?P<board_id>[0-9]+)/$', views.thumbnail),
    url('^image/(?P<board_id>[0-9]+)/marked/$', views.image, {"marked": True}),
    url('^image/(?P<board_id>[0-9]+)/voted/$', views.image, {"voted": True}),
    url('^image/(?P<board_id>[0-9]+)/$', views.image),
    url('^users/(?P<username>[^/]+)/$', views.profile),
    url('^change_theme/$', views.change_theme),
)
