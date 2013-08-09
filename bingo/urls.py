from django.conf.urls import patterns, include, url

import views

urlpatterns = patterns('',
    url('^$', views.main),
    url('^bingo/reclaim/$', views.reclaim_board),
    url('^bingo/create/$', views.create_board),
    url('^bingo/(?P<board_id>[0-9]*)/$', views.bingo),
    url('^image/(?P<board_id>[0-9]*)/$', views.image),
    url('^image/(?P<board_id>[0-9]*)/marked/$', views.image, {"marked": True}),
    url('^image/(?P<board_id>[0-9]*)/voted/$', views.image, {"voted": True}),
)
